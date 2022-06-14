//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

#include "SidelinkConfiguration.h"

#include "stack/mac/buffer/harq/LteHarqBufferRx.h"
#include "stack/mac/buffer/LteMacQueue.h"
#include "stack/mac/buffer/harq_d2d/LteHarqBufferRxD2D.h"

#include "stack/mac/scheduler/LteSchedulerUeUl.h"
#include "stack/phy/packet/SPSResourcePool.h"
#include "stack/phy/packet/cbr_m.h"
#include "stack/phy/resources/Subchannel.h"
#include "stack/mac/amc/AmcPilotD2D.h"
#include "common/LteCommon.h"
#include "stack/phy/layer/LtePhyBase.h"
#include "inet/networklayer/common/InterfaceEntry.h"
#include "inet/common/ModuleAccess.h"
#include "inet/networklayer/ipv4/IPv4InterfaceData.h"
#include "stack/mac/amc/LteMcs.h"
#include <map>
#include "stack/mac/packet/SPSResourcePoolMode4.h"
Define_Module(SidelinkConfiguration);

SidelinkConfiguration::SidelinkConfiguration()
{
    mac = NULL;
    schedulingGrant_ = NULL;
    slGrant = NULL;
}

SidelinkConfiguration::~SidelinkConfiguration()
{
    delete mac;

}

void SidelinkConfiguration::initialize(int stage)
{

    if (stage !=inet::INITSTAGE_NETWORK_LAYER_3)
        //  LteMacUeD2D::initialize(stage);
    {}

    if (stage == inet::INITSTAGE_LOCAL)
    {
        EV<<"SidelinkConfiguration::initialize, stage: "<<stage<<endl;

        resourceReservationInterval_ = par("resourceReservationInterval");
        EV<<"RRI: "<<        resourceReservationInterval_<<endl;
        minGrantStartTime_ = par("minGrantStartTime");
        maximumAllowedLatency_ = par("maximumAllowedLatency");
        currentCw_ = 0;
        maximumCapacity_ = 0;
        resourceReselectionCounter_ = par("resourceReselectionCounter");
        subchannelSize_ = par("subchannelSize");
        numSubchannels_ = par("numSubchannels");

        usePreconfiguredTxParams_ = par("usePreconfiguredTxParams");
        numberSubcarriersperPRB = par ("numberSubcarriersperPRB");
        numberSymbolsPerSlot = par("numberSymbolsPerSlot");
        bitsPerSymbolQPSK = par ("bitsPerSymbolQPSK");


        expiredGrant_ = false;

        // Register the necessary signals for this simulation


    }
    else if (stage == inet::INITSTAGE_NETWORK_LAYER_3)
    {
        deployer_ = getCellInfo(nodeId_);
        numAntennas_ = getNumAntennas();


        if (usePreconfiguredTxParams_)
        {
            preconfiguredTxParams_ = getPreconfiguredTxParams();
        }

        // LTE UE Section
        nodeId_ = getAncestorPar("macNodeId");

        //emit(macNodeID, nodeId_);

        /* Insert UeInfo in the Binder */
        ueInfo_ = new UeInfo();
        ueInfo_->id = nodeId_;            // local mac ID
        ueInfo_->cellId = cellId_;        // cell ID
        ueInfo_->init = false;            // flag for phy initialization
        ueInfo_->ue = this->getParentModule()->getParentModule();  // reference to the UE module

        // Get the Physical Channel reference of the node
        ueInfo_->phy = check_and_cast<LtePhyBase*>(ueInfo_->ue->getSubmodule("lteNic")->getSubmodule("phy"));

        // binder_->addUeInfo(ueInfo_);
    }
}



int SidelinkConfiguration::getNumAntennas()
{
    /* Get number of antennas: +1 is for MACRO */
    return deployer_->getNumRus() + 1;
}



UserTxParams* SidelinkConfiguration::getPreconfiguredTxParams()
{
    UserTxParams* txParams = new UserTxParams();

    // default parameters for D2D
    txParams->isSet() = true;
    txParams->writeTxMode(SINGLE_ANTENNA_PORT0);
    Rank ri = 1;                                              // rank for TxD is one
    txParams->writeRank(ri);
    txParams->writePmi(intuniform(1, pow(ri, (double) 2)));   // taken from LteFeedbackComputationRealistic::computeFeedback

    BandSet b;
    for (Band i = 0; i < deployer_->getNumBands(); ++i) b.insert(i);
    txParams->writeBands(b);

    RemoteSet antennas;
    antennas.insert(MACRO);
    txParams->writeAntennas(antennas);

    return txParams;
}

void SidelinkConfiguration::handleMessage(cMessage *msg)
{
    if (msg->isSelfMessage())
    {
        //LteMacUeD2D::handleMessage(msg);
        return;
    }


    cPacket* pkt = check_and_cast<cPacket *>(msg);
    cGate* incoming = pkt->getArrivalGate();


    if (msg->isName("newDataPkt"))
    {
        LteMacBase* mac = dynamic_cast<LteMacBase*>(getParentModule()->getSubmodule("mac"));
        lteInfo = check_and_cast<FlowControlInfo*>(pkt->removeControlInfo());
        if (mac->getIpBased()==false)
        {
            lteInfo->setIpBased(false);
        }

        if (mac->getIpBased()==true)
        {
            lteInfo= check_and_cast<FlowControlInfo*>(pkt->removeControlInfo());
            lteInfo->setIpBased(true);
        }

        int resourcesRequired = calculateResourceBlocks(pkt->getBitLength());

        EV<<"RBs needed for current TB: "<<resourcesRequired<<endl;

        if (slGrant == NULL ||slGrant->getExpiryTime()<NOW.dbl()||(slGrant->getTotalGrantedBlocks()<resourcesRequired))
        {
            slGrant= macGenerateSchedulingGrant(10, lteInfo->getPriority(), pkt->getBitLength());
            slGrant->setFreshAllocation(true);

        }

        else
        {
            EV<<"RBs allocated in previous grant: "<<slGrant->getTotalGrantedBlocks()<<endl;
            slGrant->setFreshAllocation(false);


            LteSidelinkGrant* phyGrant = check_and_cast<LteSidelinkGrant*> (slGrant->dup());


            LteMacBase* mac=check_and_cast<LteMacBase*>(getParentModule()->getSubmodule("mac"));
            UserControlInfo* uinfo = new UserControlInfo();

            uinfo->setSourceId(mac->getMacNodeId());
            uinfo->setDestId(mac->getMacNodeId());
            uinfo->setFrameType(SIDELINKGRANT);

            phyGrant->setDirection(D2D_MULTI);
            phyGrant->setControlInfo(uinfo);
            phyGrant->setResourceReselectionCounter(resourceReselectionCounter_-1);

            mac->sendLowerPackets( phyGrant);
        }

        slGrant->setPacketId(mac->getPacketId());
        slGrant->setCamId(mac->getCAMId());

        // Need to set the size of our grant to the correct size we need to ask rlc for, i.e. for the sdu size.
        slGrant->setGrantedCwBytes((MAX_CODEWORDS - currentCw_), pkt->getBitLength());
        slGrant->setPacketId(mac->getPacketId());

        // Mode 2 activates the grant by default and uses all the resource blocks allocated
        slGrant->setActivateGrant(true);
        slGrant->setSubsetRbActivate(resourcesRequired);
        setSidelinkGrant(slGrant);

    }


}

//Mode 1 configured Grant assignment

void SidelinkConfiguration::assignGrantToData(DataArrival* pkt, std::string rrcState)
{
    rrcCurrentState = rrcState;
    LteMacBase* mac = dynamic_cast<LteMacBase*>(getParentModule()->getSubmodule("mac"));

    if(rrcState=="RRC_CONN" || rrcState=="RRC_INACTIVE")
    {

        UserControlInfo* lteInfo = check_and_cast< UserControlInfo*>(pkt->removeControlInfo());
        int tbSize = pkt->getDataSize();

        int resourcesRequired = calculateResourceBlocks(tbSize);

        EV<<"RBs needed for current TB: "<<resourcesRequired<<endl;
        if (slGrant == NULL ||slGrant->getExpiryTime()<NOW.dbl()||(slGrant->getTotalGrantedBlocks()<resourcesRequired))
        {
            slGrant= macGenerateSchedulingGrant(resourcesRequired+5, lteInfo->getPriority(), tbSize);
            slGrant->setSubsetRbActivate(resourcesRequired);

        }
        else
        {
            EV<<"RBs allocated in previous grant: "<<slGrant->getTotalGrantedBlocks()<<endl;
            slGrant->setFreshAllocation(false);


            LteSidelinkGrant* phyGrant = check_and_cast<LteSidelinkGrant*> (slGrant->dup());


            LteMacBase* mac=check_and_cast<LteMacBase*>(getParentModule()->getSubmodule("mac"));
            UserControlInfo* uinfo = new UserControlInfo();

            uinfo->setSourceId(mac->getMacNodeId());
            uinfo->setDestId(mac->getMacNodeId());
            uinfo->setFrameType(SIDELINKGRANT);

            phyGrant->setDirection(D2D_MULTI);
            phyGrant->setControlInfo(uinfo);
            phyGrant->setResourceReselectionCounter(resourceReselectionCounter_-1);

            //Activating only a subset - future allocations and aperiodic traffic but size smaller that what is available in grant
            phyGrant->setSubsetRbActivate(resourcesRequired);

            mac->sendLowerPackets( phyGrant);
        }

        slGrant->setPacketId(mac->getPacketId());
        slGrant->setCamId(mac->getCAMId());

        // Need to set the size of our grant to the correct size we need to ask rlc for, i.e. for the sdu size.
        slGrant->setGrantedCwBytes((MAX_CODEWORDS - currentCw_), pkt->getBitLength());
        slGrant->setPacketId(mac->getPacketId());


    }
    //throw cRuntimeError("SidelinkConfiguration::assignGrantToData");
}




void SidelinkConfiguration::handleSelfMessage()
{
    //integrated with LteMacUeD2D::handleSelfMessage();
}

void SidelinkConfiguration::macHandleSps(std::vector<std::tuple<double, int, double>> CSRs, std::string rrcCurrentState)
{
    /* *   This is where we add the subchannels to the actual scheduling grant, so a few things
     * 1. Need to ensure in the self message part that if at any point we have a scheduling grant without assigned subchannels, we have to wait
     * 2. Need to pick at random from the SPS list of CSRs
     * 3. Assign the CR
     * 4. return
     * */


    //SPSResourcePool* candidatesPacket = check_and_cast<SPSResourcePool *>(pkt);
    slGrant = getSidelinkGrant();

    EV<<"Number of CSRs: "<<CSRs.size()<<endl;

    //slGrant = check_and_cast<LteSidelinkGrant*>(schedulingGrant_);

    // Select random element from vector
    int index=0;

    if (CSRs.size()==0)
    {
        EV<<"CSRs size: "<<CSRs.size()<<endl;
        throw cRuntimeError("Cannot allocate CSRs");
    }

    index = intuniform(0, CSRs.size()-1, 1);

    std::tuple<double, int, double> selectedCR = CSRs[index];
    // Gives us the time at which we will send the subframe.


    int initialSubchannel = 0;
    int finalSubchannel = initialSubchannel + slGrant->getNumSubchannels(); // Is this actually one additional subchannel?

    EV<<"initial subchannel: "<<initialSubchannel<<" "<<"final subchannel: "<<finalSubchannel<<endl;

    // Determine the RBs on which we will send our message

    int totalGrantedBlocks = slGrant->getTotalGrantedBlocks();
    double startTime= slGrant->getStartTime().dbl();

    slGrant->setPeriodic(true);
    //slGrant->setTotalGrantedBlocks(totalGrantedBlocks);

    slGrant->setDirection(D2D_MULTI);
    slGrant->setCodewords(1);
    slGrant->setStartingSubchannel(initialSubchannel);

    mod = _QPSK;
    EV<<"totalGrantedBlocks: "<<totalGrantedBlocks<<endl;
    setAllocatedBlocksSCIandData(totalGrantedBlocks);

    unsigned int i = (mod == _QPSK ? 0 : (mod == _16QAM ? 9 : (mod == _64QAM ? 15 : 0)));


    const unsigned int* tbsVect = itbs2tbs(mod, SINGLE_ANTENNA_PORT0, 1, 7 - i);
    maximumCapacity_ = tbsVect[10-1];//totalGrantedBlocks=10


    slGrant->setGrantedCwBytes(currentCw_, maximumCapacity_);
    // Simply flips the codeword.
    currentCw_ = MAX_CODEWORDS - currentCw_;

    EV<<"Sidelink Configuration Granted CWBytes size: "<<slGrant->getGrantedCwBytesArraySize()<<endl;
    //Implement methods to store expiration counter and period counter

    setSidelinkGrant(slGrant);

    // TODO: Setup for HARQ retransmission, if it can't be satisfied then selection must occur again.
    CSRs.clear();

}

LteSidelinkGrant* SidelinkConfiguration::macGenerateSchedulingGrant(double maximumLatency, int priority, int tbSize)
{
    /**
     * 1. Packet priority
     * 2. Resource reservation interval
     * 3. Maximum latency
     * 4. Number of subchannels
     * 6. Send message to PHY layer looking for CSRs
     */
    EV<<"SidelinkConfiguration::macGenerateSchedulingGrant"<<endl;
    if(rrcCurrentState=="RRC_CONN" ||rrcCurrentState=="RRC_INACTIVE")
    {
        slGrant = new LteSidelinkGrant("LteMode3Grant");
    }

    else
    {
        slGrant = new LteSidelinkGrant("LteMode4Grant");
    }

    minGrantStartTime_ = intuniform(0,4);
    // Priority is the most difficult part to figure out, for the moment I will assign it as a fixed value
    slGrant -> setPriority(priority);
    slGrant -> setRri(resourceReservationInterval_); //resource reservation interval/Prsvp_TX
    maximumAllowedLatency_ = intuniform(20,100);  //Uniformly varies between 20 ms and 100 ms
    slGrant->setMinGrantStartTime(minGrantStartTime_);
    slGrant -> setMaximumLatency(maximumAllowedLatency_);
    slGrant->setStartingSubchannel(0);

    // Selecting the number of subchannel at random as there is no explanation as to the logic behind selecting the resources in the range unlike when selecting MCS.
    //slGrant -> setNumberSubchannels(25); allocation

    // Based on restrictResourceReservation interval But will be between 1 and 15
    // Again technically this needs to reconfigurable as well. But all of that needs to come in through ini and such.


    if (0<resourceReservationInterval_<100)
    {
        resourceReselectionCounter_ = 10;
    }
    else if (resourceReservationInterval_ >=100)

    {
        resourceReselectionCounter_ = 10; // Beacuse RRI = 100ms
    }

    else
    {
        resourceReselectionCounter_ = 0;
    }
    slGrant -> setResourceReselectionCounter(resourceReselectionCounter_);
    slGrant -> setExpiryTime(NOW.dbl()+0.1*(resourceReselectionCounter_-1));
    slGrant->setTransmitBlockSize(tbSize);
    slGrant->setRri(resourceReservationInterval_);
    slGrant->setMinGrantStartTime(minGrantStartTime_);
    slGrant->setRetransmission(false);
    slGrant->setTimeGapTransRetrans(0);
    slGrant->setTotalGrantedBlocks(0); // Initialize (to be allocated by SRA module)
    slGrant->setTotalGrantedBlocks(calculateResourceBlocks(tbSize));
    slGrant->setFreshAllocation(true);
    LteSidelinkGrant* phyGrant = slGrant;

    LteMacBase* mac=check_and_cast<LteMacBase*>(getParentModule()->getSubmodule("mac"));
    UserControlInfo* uinfo = new UserControlInfo();

    uinfo->setSourceId(mac->getMacNodeId());
    uinfo->setDestId(mac->getMacNodeId());
    uinfo->setFrameType(SIDELINKGRANT);

    phyGrant->setDirection(D2D_MULTI);
    phyGrant->setControlInfo(uinfo);

    mac->sendLowerPackets( phyGrant);
    schedulingGrant_ = slGrant;

    setSidelinkGrant(slGrant);
    return slGrant;

}

void SidelinkConfiguration::flushHarqBuffers(HarqTxBuffers harqTxBuffers_, LteSidelinkGrant* grant)
{
    // send the selected units to lower layers
    // First make sure packets are sent down
    // HARQ retrans needs to be taken into account
    // Maintain unit list maybe and that causes retrans?
    // But purge them once all messages sent.
    int mcsCapacity = 0;
    slGrant = grant;

    //slGrant = dynamic_cast<LteSidelinkGrant*>(schedulingGrant_);

    HarqTxBuffers::iterator it2;
    EV<<"Harq size: "<<harqTxBuffers_.size()<<endl;
    EV<<"Scheduling grant: "<<slGrant<<endl;

    for(it2 = harqTxBuffers_.begin(); it2 != harqTxBuffers_.end(); it2++)
    {
        EV<<"SidelinkConfiguration::flushHarqBuffers for: "<<it2->second->isSelected()<<endl;



        std::unordered_map<std::string,double>::const_iterator got;

        if (it2->second->isSelected())
        {
            //throw cRuntimeError("debug 3");
            LteHarqProcessTx* selectedProcess = it2->second->getSelectedProcess();

            for (int cw=0; cw<MAX_CODEWORDS; cw++)
            {

                int pduLength = selectedProcess->getPduLength(cw);
                EV<<"PDU length: "<<pduLength<<endl;

                mod = _QPSK;

                unsigned int i = (mod == _QPSK ? 0 : (mod == _16QAM ? 9 : (mod == _64QAM ? 15 : 0)));

                const unsigned int* tbsVect = itbs2tbs(mod, SINGLE_ANTENNA_PORT0, 1, 1 - i);
                mcsCapacity = tbsVect[10-1];
                EV<<" mcsCapacity: "<< mcsCapacity <<endl;
                // throw cRuntimeError("flushHarq");

                EV<<"Valid MCS found: "<<endl;
                foundValidMCS = true;

                slGrant->setMcs(1);

                slGrant->setGrantedCwBytes(cw, mcsCapacity);

                if (! slGrant->getUserTxParams())
                {
                    slGrant->setUserTxParams(preconfiguredTxParams_);
                }

                // Send pdu to PHY layer for sending.
                it2->second->sendSelectedDown();

                // Log transmission to A calculation log
                previousTransmissions_[NOW.dbl()] =  slGrant->getNumSubchannels();

                //emit(selectedMCS, mcs);
                EV<<"VALID MCS: "<<foundValidMCS<<endl;


            }
            if (!foundValidMCS)
            {
                //throw cRuntimeError("debug 5");
                // Never found an MCS to satisfy the requirements of the message must regenerate grant
                //slGrant = check_and_cast<LteSidelinkGrant*>(schedulingGrant_);

                simtime_t elapsedTime = NOW - receivedTime_;


                if (elapsedTime<= 0)
                {
                    //emit(droppedTimeout, 1);
                    selectedProcess->forceDropProcess();
                    delete schedulingGrant_;
                    schedulingGrant_ = NULL;
                }
                else
                {
                    delete schedulingGrant_;
                    schedulingGrant_ = NULL;
                    //macGenerateSchedulingGrant(remainingTime_, priority, 0);
                }
            }
        }
        break;
    }



    if (expiredGrant_) {
        // Grant has expired, only generate new grant on receiving next message to be sent.
        delete schedulingGrant_;
        schedulingGrant_ = NULL;
        expiredGrant_ = false;
    }

}

int SidelinkConfiguration::calculateResourceBlocks(int tbSize)
{
    EV<<"Calculating the numer of PRBs needed for Transport block ..."<<endl;
    int numberSymbolsPerPRB= numberSubcarriersperPRB*numberSymbolsPerSlot*bitsPerSymbolQPSK;
    int numberSymbolsTransmitBlock = tbSize/bitsPerSymbolQPSK;

    EV<<"Data size: "<<tbSize<<endl;
    EV<<"numberSymbolsPerPRB: "<<numberSymbolsPerPRB<<endl;

    numberPRBTransmitBlock = (numberSymbolsTransmitBlock/numberSymbolsPerPRB)+1;
    EV<<"numberSymbolsTransmitBlock "<<numberSymbolsTransmitBlock <<endl;

    return numberPRBTransmitBlock;

}

void SidelinkConfiguration::setAllocatedBlocksSCIandData(int totalGrantedBlocks)
{
    allocatedBlocksSCIandData = totalGrantedBlocks;
}


void SidelinkConfiguration::finish()
{

}

void SidelinkConfiguration::setSidelinkGrant(LteSidelinkGrant* slGrant)
{
    slGrant = slGrant;
}


