
#include "SidelinkResourceAllocation.h"
#include <math.h>
#include <assert.h>
#include <algorithm>
#include <iterator>
#include <vector>
#include <tuple>
#include <tuple>
#include "stack/phy/resources/SidelinkResourceAllocation.h"
#include "stack/phy/packet/LteFeedbackPkt.h"
#include "stack/d2dModeSelection/D2DModeSelectionBase.h"
#include "stack/phy/packet/SPSResourcePool.h"
#include "stack/phy/packet/cbr_m.h"
#include <unordered_map>
#include "common/LteControlInfo.h"
#include "stack/mac/configuration/SidelinkConfiguration.h"

using namespace std;




Define_Module(SidelinkResourceAllocation);

SidelinkResourceAllocation::SidelinkResourceAllocation()
{
    handoverStarter_ = NULL;
    handoverTrigger_ = NULL;
    RBIndicesSCI.clear();
    RBIndicesData.clear();

}

SidelinkResourceAllocation::~SidelinkResourceAllocation()
{

}
void SidelinkResourceAllocation::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage())
    {
        EV<<"SidelinkResourceAllocation::handleMessage()"<<endl;
        handleSelfMessage(msg);

    }
}
void SidelinkResourceAllocation::initialize(int stage)
{

    if (stage == inet::INITSTAGE_LOCAL)
    {
        EV<<"SidelinkResourceAllocation::initialize, stage: "<<stage<<endl;
        adjacencyPSCCHPSSCH_ = par("adjacencyPSCCHPSSCH");
        pStep_ = par("pStep");
        selectionWindowStartingSubframe_ = par("selectionWindowStartingSubframe");
        numSubchannels_ = par("numSubchannels");
        subchannelSize_ = par("subchannelSize");
        d2dDecodingTimer_ = NULL;
        transmitting_ = false;
        numberSubcarriersperPRB = par ("numberSubcarriersperPRB");
        numberSymbolsPerSlot = par("numberSymbolsPerSlot");
        bitsPerSymbolQPSK = par ("bitsPerSymbolQPSK");
        //int thresholdRSSI = 50;
        subChRBStart_ = par ("subChRBStart");
        //thresholdRSSI_ = (-112 + 2 * thresholdRSSI);
        rsrpThreshold_ = par("rsrpThreshold");
        rssiThreshold_=par("rssiThreshold");
        nodeType_=aToNodeType(par("nodeType"));
        EV<<"SRA nodetype: "<<nodeType_<<endl;
        numberPRBSCI = 2;
        d2dTxPower_ = par("d2dTxPower");
        if (d2dTxPower_ <= 0){
            d2dTxPower_ = txPower_;
        }
        nodeId_ = getAncestorPar("macNodeId");
        // The threshold has a size of 64, and allowable values of 0 - 66
        // Deciding on this for now as it makes the most sense (low priority for both then more likely to take it)
        // High priority for both then less likely to take it.
        for (int i = 1; i < 66; i++)
        {
            ThresPSSCHRSRPvector_.push_back(i);
        }

        numberSubchannels = registerSignal("numberSubchannels");
        totalCSR = registerSignal("totalCSR");
        syncLatency = registerSignal("syncLatency");
        resourceAllocationLatency = registerSignal("resourceAllocationLatency");
        configurationLatency = registerSignal("configurationLatency");
        halfDuplexError = registerSignal("halfDuplex");
        pcMode4 = registerSignal("packetCollisionMode4");
        sciReceived_ = 0;
        sciDecoded_ = 0;
        sciNotDecoded_ = 0;
        sciFailedHalfDuplex_ = 0;
        tbReceived_ = 0;
        tbDecoded_ = 0;
        tbFailedDueToNoSCI_ = 0;
        tbFailedButSCIReceived_ = 0;
        tbAndSCINotReceived_ = 0;
        tbFailedHalfDuplex_ = 0;
        subchannelReceived_ = 0;
        subchannelsUsed_ = 0;
        countHD=0;
        sensingWindowFront_ = 0; // Will ensure when we first update the sensing window we don't skip over the first element
        allocatedBlocksPrevious = 0;
        cResel =0;
        pcCountMode4 = 0;
        packetDrop = false;

    }
    else if (stage == inet::INITSTAGE_NETWORK_LAYER_2)
    {
        initialiseSensingWindow();
        setReselectionCounter(cResel);
        sidelinkSynchronization(packetDrop);
        occupiedResourceBlocks= RBIndicesSCI.size()+RBIndicesData.size();
        initialiseCbrWindow();
        initialiseFreqAllocationMap();
    }

}

void SidelinkResourceAllocation::handleSelfMessage(cMessage *msg)
{

    if (msg->isName("SLSS"))
    {
        //Start sidelink synchronization
        EV<<"SLSS self"<<endl;
        sidelinkSynchronization(packetDrop);
    }
    else if (msg->isName("SIB21PreConfigured"))
    {

        EV<<"SidelinkResourceAllocation::handleSelfMessage() SIB 21"<<endl;

    }
    else
    {
        delete msg;
    }
}


void SidelinkResourceAllocation::handleUpperMessage(cMessage* msg)
{
    EV<<"SidelinkResourceAllocation::handleUpperMessage: "<<msg->getName()<<endl;
    UserControlInfo* lteInfo = check_and_cast<UserControlInfo*>(msg->removeControlInfo());

    /*    if (msg->isName("LteMode4Grant") )
    {
        nodeType_ = UE;}
    else if ( msg->isName("LteMode3Grant"))
    {
        nodeType_ = ENODEB;
    }*/

    if (lteInfo->getFrameType() == SIDELINKGRANT)
    {
        // Generate CSRs or save the grant use when generating SCI information
        LteSidelinkGrant* grant = check_and_cast<LteSidelinkGrant*>(msg);
        /*            for (int i=0; i<numSubchannels_; i++)
            {
                // Mark all the subchannels as not sensed
                sensingWindow_[sensingWindowFront_][i]->setSensed(false);
            }*/
        cResel = getReselectionCounter();
        setReselectionCounter(cResel);
        EV<<"Number of previously granted blocks: "<<getAllocatedBlocksPrevious()<<"previous cResel: "<<cResel<<endl;

        EV<<"Node type: "<<nodeType_<<endl;
        //Mode 4
        if (nodeType_ ==UE )
        {

            if (getAllocatedBlocksPrevious() > 0 && cResel>0)
            {

                //Check if data size fits into previously allocated TB size
                int numberSymbolsPerPRB= numberSubcarriersperPRB*numberSymbolsPerSlot*bitsPerSymbolQPSK;
                int numberSymbolsTransmitBlock = grant->getTransmitBlockSize()/bitsPerSymbolQPSK;
                numberPRBTransmitBlock = (numberSymbolsTransmitBlock/numberSymbolsPerPRB)+1;
                int numberPRBNeeded =   numberPRBTransmitBlock+2; //SCI+TB

                if (numberPRBNeeded<=getAllocatedBlocksPrevious()) //" RBs for SCI
                {
                    //Use previous subchannels for the current subframes
                    RBIndicesData =  getPreviousSubchannelsData();
                    EV<<"Using previously allocated subchannels for data and SCI"<<  RBIndicesData.size()<<endl;
                    //determine the subframe
                    computeCSRs(grant,nodeType_);

                    return;
                }
                if (numberPRBNeeded>getAllocatedBlocksPrevious()) //" RBs for SCI
                {
                    EV<<"Data size does not fit into previous allocation, need for re-allocation"<<endl;

                    //Reset counter and previous allocations
                    cResel=0;
                    //setReselectionCounter(cResel);
                    setAllocatedBlocksPrevious(0);
                    computeCSRs(grant,nodeType_);
                    return;
                }
                return;

            }
            //This if loop should check for cResel - alloctaion for first time and re-allocation based on cResel
            if (getAllocatedBlocksPrevious() == 0 || cResel==0)
            {
                // Generate a vector of CSRs and send it to the MAC layer
                EV<<"Calling computeSCRs()"<<grant->getTransmitBlockSize()<<endl;
                computeCSRs(grant,nodeType_);
                //delete lteInfo;
                //delete grant;
                sciGrant_ = grant;
                lteInfo->setUserTxParams(sciGrant_->getUserTxParams());
                lteInfo->setGrantedBlocks(sciGrant_->getGrantedBlocks());
                lteInfo->setDirection(D2D_MULTI);
                return;
            }
        }

        //Mode 3
        if (nodeType_==ENODEB)
        {
            EV<<"Sidelink resource allocation according to mode 3"<<endl;
            computeCSRs(grant,nodeType_);
            return;
        }



    }

    else if (lteInfo->getFrameType() == HARQPKT)
    {
        LteAirFrame* frame = new LteAirFrame("harqFeedback-grant");
    }
    else
    {
        throw cRuntimeError("Invalid grant");
    }


}

//5G Mode 2 resource allocation

//Stage 1 SCI

LteAirFrame* SidelinkResourceAllocation::createSCIMessage(cMessage* msg, LteSidelinkGrant* grant)
{
    EV << NOW << " SidelinkResourceAllocation::createSCIMessage - Start creating SCI..." << endl;

    SidelinkControlInformation* sci = new SidelinkControlInformation("SCI Message");

    /*
     * Priority - takes values 0-7. It depends on the nature of the application. It is defined at the upper layers.

     */
    //
    sci->setPriority(grant->getSpsPriority());

    /* Resource reservation interval/Prsvp_TX
     *
     * 0 -> 16
     * 0 = not reserved
     * 1 = 100ms (1) RRI [Default]
     * 2 = 200ms (2) RRI
     * ...
     * 10 = 1000ms (10) RRI
     * 11 = 50ms (0.5) RRI
     * 12 = 20ms (0.2) RRI
     * 13 - 15 = Reserved
     *
     */
    if (grant->getExpiration() != 0)
    {
        sci->setResourceReservationInterval(0.1); //100 ms for cResel = [5,15]
    }
    else
    {
        sci->setResourceReservationInterval(0);
    }

    /* Frequency Resource Location for initial transmissiona nd re-transmission
     * Based on another parameter RIV
     * but size is
     * Log2(Nsubchannel(Nsubchannel+1)/2) (rounded up)
     * 0 - 8 bits
     * 0 - 256 different values
     *
     * Based on TS36.213 14.1.1.4C
     *     if SubchannelLength -1 < numSubchannels/2
     *         RIV = numSubchannels(SubchannelLength-1) + subchannelIndex
     *     else
     *         RIV = numSubchannels(numSubchannels-SubchannelLength+1) + (numSubchannels-1-subchannelIndex)
     */

    unsigned  int riv;
    //
    if (grant->getNumSubchannels() -1 <= (numSubchannels_/2))
    {
        // RIV calculation for less than half+1
        riv = ((numSubchannels_ * (grant->getNumSubchannels() - 1)) + grant->getStartingSubchannel());
    }
    else
    {

        // RIV calculation for more than half size
        riv = ((numSubchannels_ * (numSubchannels_ - grant->getNumSubchannels() + 1)) + (numSubchannels_ - 1 - grant->getStartingSubchannel()));
    }

    sci->setFrequencyResourceLocation(riv);

    /* TimeGapRetrans
     * 1 - 15
     * ms from init to retrans
     */
    sci->setTimeGapRetrans(grant->getTimeGapTransRetrans());


    /* mcs
     * 5 bits
     * 26 combos
     * Technically the MAC layer determines the MCS that it wants the message sent with and as such it will be in the packet
     */
    sci->setMcs(grant->getMcs());

    /* retransmissionIndex
     * 0 / 1
     * if 0 retrans is in future/this is the first transmission
     * if 1 retrans is in the past/this is the retrans
     */
    if (grant->getRetransmission())
    {
        sci->setRetransmissionIndex(1);
    }
    else
    {
        sci->setRetransmissionIndex(0);
    }
    //cResel = grant->getResourceReselectionCounter();


    //sci->setCResel(grant->getResourceReselectionCounter());
    //cResel = grant->getResourceReselectionCounter();
    //setReselectionCounter(cResel);

    /* Filler up to 32 bits
     * Can just set the length to 32 bits and ignore the issue of adding filler
     */
    sci->setBitLength(32);

    //Print all SCI values
    EV<<"Priority: "<<grant->getSpsPriority()<<endl;
    EV<<"Resource Reservation Interval: "<<(grant->getPeriod()/100)<<endl;
    EV<<"Frequency resource location of initial transmission and re-transmission (RIV): "<<riv<<endl;
    EV<<"Subframe gap: "<<grant->getTimeGapTransRetrans()<<endl;
    EV<<"Modulation and Coding Scheme: "<<grant->getMcs()<<endl;
    EV<<"Re-transmission index: "<<sci->getRetransmissionIndex()<<endl;
    //EV<<"Re-selection counter: "<<getReselectionCounter()<<endl;

    UserControlInfo* lteInfo = new UserControlInfo();
    lteInfo->setGrantStartTime(grant->getStartTime());
    LteAirFrame* sciFrame = prepareAirFrame(sci, lteInfo);
    return sciFrame;

}

LteAirFrame* SidelinkResourceAllocation::prepareAirFrame(cMessage* msg, UserControlInfo* lteInfo){
    // Helper function to prepare airframe for sending.

    EV<<"SidelinkResourceAllocation::prepareAirFrame"<<nodeId_<<endl;
    LteAirFrame* frame = new LteAirFrame("SCIframe");
    frame->encapsulate(check_and_cast<cPacket*>(msg));
    frame->setSchedulingPriority(10); //Airframe priority = 10 as defined in LtePhyBase
    frame->setDuration(TTI);

    LtePhyBase* phy=check_and_cast<LtePhyBase*>(getParentModule()->getSubmodule("phy"));

    lteInfo->setSourceId(nodeId_);
    lteInfo->setCoord(phy->getCoord());
    lteInfo->setFrameType(SCIPKT);
    lteInfo->setDirection(D2D_MULTI);
    lteInfo->setTxPower(txPower_);
    lteInfo->setD2dTxPower(d2dTxPower_);
    frame->setControlInfo(lteInfo);
    return frame;
}


std::vector<int> SidelinkResourceAllocation::getallocationTBIndex(int bitLength, std::vector<int> subChSCI)
{
    allocatedPRBTBIndex.clear();

    int numberSymbolsPerPRB= numberSubcarriersperPRB*numberSymbolsPerSlot*bitsPerSymbolQPSK;
    int numberSymbolsTransmitBlock = bitLength/bitsPerSymbolQPSK;
    numberPRBTransmitBlock = (numberSymbolsTransmitBlock/numberSymbolsPerPRB)+1;

    //Allocate PRBs for TB contiguously after SCI

    int startSubChTB = subChSCI.at(1)+1;
    int beta = 2;
    EV<<"startSubChTB"<<subChSCI[0]<<" "<<subChSCI[1]<<endl;

    EV<<" numberPRBTransmitBlock: "<< numberPRBTransmitBlock<<endl;
    for (int j=0; j<numberPRBTransmitBlock; j++)
    {


        EV<<"TB indices: "<<startSubChTB+j<<endl;
        allocatedPRBTBIndex.push_back(startSubChTB+j);

        if (!adjacencyPSCCHPSSCH_)
        {
            allocatedPRBSciIndex.push_back(subChRBStart_ + numberPRBSCI*subchannelSize_+j+beta);
        }
    }

    setAllocatedPrbtbIndex(allocatedPRBTBIndex);
    return allocatedPRBTBIndex;

}

std::vector<int>  SidelinkResourceAllocation::getallocationSciIndex(int subChRBStart_)
{
    allocatedPRBSciIndex.clear();
    RbMap sciRbs;

    // Setup so SCI gets 2 RBs from the grantedBlocks.
    RbMap::iterator it;
    std::map<Band, unsigned int>::iterator jt;

    //for each Remote unit used to transmit the packet
    int allocatedBlocks = 0;



    //Allocate twp PRBS for SCI
    for (int j=0; j<2; j++)
    {
        EV<<"SCI indices: "<<subChRBStart_ + j<<endl;
        allocatedPRBSciIndex.push_back(subChRBStart_ + j);
    }

    setAllocatedPrbSciIndex(allocatedPRBSciIndex);
    return allocatedPRBSciIndex;
}

void SidelinkResourceAllocation::computeCSRs(LteSidelinkGrant* grant, LteNodeType nodeType_) {
    candidateSubframes.clear();
    futureTransmissions.clear();
    //Re-allocate subchannels and subframes
    RBIndicesSCI.clear();
    RBIndicesData.clear();
    resourceAllocationMap.clear();

    //Computing subframes
           int startSubFrame = intuniform(0,4);
           double maxLatency = grant->getMaximumLatency();
           EV<<"Max latency: "<<maxLatency<<endl;
           int endSubFrame = startSubFrame+maxLatency;
           int selectionWindow =  maxLatency - startSubFrame;
           //int possibleCSRSSelWindow;
           EV<<"Start subframe: "<<startSubFrame<<endl;
           EV<<"End subframe: "<<endSubFrame<<endl;

           //Discarding subframes where sync information appears - PSSS,SSSS,DMRS
           EV<<"Next SLSS: "<<nextSLSS<<endl;
           simtime_t selStartTime;
           simtime_t selEndTime;
           //Converting to ms
           selStartTime = (NOW+TTI+startSubFrame/1000.0) .trunc(SIMTIME_MS);
           selEndTime =  (selStartTime+(100/1000.0)).trunc(SIMTIME_MS);

           if (nodeType_ == ENODEB)

           {
               selStartTime = (NOW+nextSLSS+TTI+startSubFrame/1000.0) .trunc(SIMTIME_MS);
               selEndTime =  (selStartTime+(100/1000.0)).trunc(SIMTIME_MS);

           }


           if (nodeType_==UE )

           {
               EV<<"packetDropStatus: "<<packetDrop<<endl;
               if (packetDrop==false)
               {
                   selStartTime = (nextSLSS+TTI+startSubFrame/1000.0) .trunc(SIMTIME_MS);
                   selEndTime =  (selStartTime+(100/1000.0)).trunc(SIMTIME_MS);

               }
               if (packetDrop==true)
               {
                   selStartTime = (NOW+TTI+startSubFrame/1000.0) .trunc(SIMTIME_MS);
                   selEndTime =  (selStartTime+(100/1000.0)).trunc(SIMTIME_MS);
               }

           }

           tSync = (nextSLSS+0.001-NOW).dbl();  //it takes one TTI for SLSS acknowledgement
           EV<<"Synchronization latency: "<<tSync<<endl;
           emit(syncLatency,tSync);

           EV<<"selectionWindow start time:  "<<selStartTime<<endl;
           EV<<"selectionWindow end time:  "<<selEndTime<<endl;

           emit(configurationLatency,0.004);

           for (double k = selStartTime.dbl(); k<=selEndTime.dbl(); k=k+TTI)
           {
               candidateSubframes.push_back(k);

           }
           EV<<"Number of candidate subframes: "<< candidateSubframes.size()<<endl;

    if (packetDrop==false && (getAllocatedBlocksPrevious() == 0 || cResel==0)  )
    {

        //Fresh allocations
        cResel = grant->getResourceReselectionCounter();


        /*EV<<"Retrieve cResel: "<<getReselectionCounter()<<endl;*/
        subChRBStart_ = intuniform(0,std::ceil((numSubchannels_*subchannelSize_)/2)-1);

        EV<<"Start of subchannel: "<<subChRBStart_<<endl;

        RBIndicesSCI=getallocationSciIndex(subChRBStart_);
        RBIndicesData=getallocationTBIndex(grant->getTransmitBlockSize(),  RBIndicesSCI);

        grant->setStartingSubchannel(subChRBStart_);


        EV<<"Allocating CSRs for : "<<nodeTypeToA(nodeType_)<<endl;


        int totalPRBsPerSubframe = 0;
        totalPRBsPerSubframe = RBIndicesSCI.size()+RBIndicesData.size();

        grant->setTotalGrantedBlocks(totalPRBsPerSubframe);
        EV<<"Total number of RBs for SCI+Data: "<<totalPRBsPerSubframe<<endl;

        cbr = calculateChannelBusyRatio(totalPRBsPerSubframe);
        //Compute average CBR measured over past 100 subframes
        averageCbr = 0.0;
        cbrWindow = getCbrWindow();
        for (auto [X, Y]:cbrWindow)
        {
            averageCbr= averageCbr+Y;
        }
        averageCbr = averageCbr/cbrWindow.size();
        //cr = calculateChannelOccupancyRatio();
        crLimitReached = checkCRLimit(averageCbr,cr);


        binder_ = getBinder();
        std::map<MacNodeId,inet::Coord> broadcastUeMap = binder_->getBroadcastUeInfo();

        EV<<"broadcastUeMap: "<<broadcastUeMap.size()<<endl;

        std::map<MacNodeId,inet::Coord>::iterator itb = broadcastUeMap.begin();



        boost::circular_buffer<std::tuple<double, double,double,bool,bool>> sensingWindowSubframes = getSensingWindow();
        unsigned int Prsvp_TX = grant->getPeriod(); //Resource reservation interval
        unsigned int  Prsvp_TX_prime = 0.1;

        EV<<"Re-selection counter: "<<cResel<<endl;

        double ySensing;
        std::vector<double> zSelection;
        zSelection.clear();
        auto itc=sensingWindowSubframes.begin();
        for (;itc != sensingWindowSubframes.end();++itc)
        {
            //Previous transmission or reception in sensing window
            if((get<2>(*itc)==true)||(get<3>(*itc)==true))
            {
                ySensing = get<0>(*itc);
                // EV<<"Subframes to be checked: "<<ySensing<<endl;
                for(int j=0;j<cResel-1;j++)
                {
                    zSelection.push_back(ySensing+j*0.1);
                    //EV<<"Subframes to be removed from selection window: "<<ySensing+j*0.1<<endl;
                }
            }
        }


        for (auto & iter : zSelection)
        {
            EV<<"value to be compared: "<<iter<<endl;

            for (auto  &it:candidateSubframes)
            {

                if(std::abs(it -iter) < 0.0001)
                {
                    EV<<"Match: "<<it<<endl;
                    //Erase from candidate subframe
                    int index =  &it - &candidateSubframes[0];
                    EV<<"Matching index: "<<index<<endl;
                    candidateSubframes.erase(candidateSubframes.begin()+index);
                }
            }
        }

        //Print final selection window
        /*    for  (auto csr:candidateSubframes )
    {
        EV<<"Final selection window: "<<csr<<endl;
    }*/

        EV<<"Final selection window size: "<<candidateSubframes.size()<<endl;

        int randomIndexInitial = rand() % candidateSubframes.size();
        simtime_t startFirstTransmission = candidateSubframes[randomIndexInitial];

        EV<<"First transmission: "<<startFirstTransmission<<endl;

        grant->setTotalGrantedBlocks(RBIndicesSCI.size()+RBIndicesData.size());
        setPreviousSubchannelsData(RBIndicesData);
        EV<<"Set total granted blocks: "<<grant->getTotalGrantedBlocks()<<endl;
        EV<<"First transmission: "<<startFirstTransmission<<endl;
        grant->setStartTime(startFirstTransmission);
        FirstTransmission = startFirstTransmission.dbl();
        setFirstTransmissionPrevious(FirstTransmission);
        binder_->updatePeriodicCamTransmissions(nodeId_,startFirstTransmission.dbl());

        EV<<"Resource allocation latency: "<<(startFirstTransmission-selStartTime).dbl()<<endl;
        //optimalCSRs=selectBestRSSIs(eraseSubframe, grant,NOW.dbl());
        resourceAllocationLatency = (startFirstTransmission-selStartTime).dbl();
        emit(resourceAllocationLatency,(startFirstTransmission-selStartTime).dbl());



        for (int k=0; k<candidateSubframes.size();k++)
        {
            optimalCSRs.emplace_back(0,totalPRBsPerSubframe,candidateSubframes[k]);
        }
    }

    else {

//Subsequent allocations
            cResel = getReselectionCounter();
            FirstTransmission = getFirstTransmissionPrevious()+0.1;//increment by RRI for subsequent packet transmissions
            setFirstTransmissionPrevious(FirstTransmission);
            grant->setTotalGrantedBlocks(getAllocatedBlocksPrevious());
            EV<<"First transmission subsequent: "<< FirstTransmission<<endl;
            binder_->updatePeriodicCamTransmissions(nodeId_, FirstTransmission);
            grant->setStartTime( FirstTransmission);

    }
    //Make sure allocations are within CR limits and only then update in the FreqAllocationMap buffer
    updateFreqAllocationMap(FirstTransmission,grant->getTotalGrantedBlocks());
    double crValue=calculateChannelOccupancyRatio(getFreqAllocationMap(),getReselectionCounter());
    EV<<"CRValue: "<<crValue<<endl;
    EV<<"crLimit: "<<crLimit<<endl;

/*    if ((crValue-crLimit)>0.0)
    {
        updateFreqAllocationMap(FirstTransmission,grant->getTotalGrantedBlocks());
    }
    else
    {
        EV<<"Congestion detected: "<<endl;
        //Implement range control approach to control congestion
    }*/

    grant->setNextArrival(NOW.dbl()+0.1);

    EV<<"Start time grant: "<<grant->getStartTime()<<endl;
    EV<<"Next arrival grant: "<<grant->getNextArrival()<<endl;


/*
    if ((grant->getStartTime()>grant->getNextArrival())||(grant->getStartTime().dbl() < selStartTime.dbl()))
    {
        EV<<"Activating packet drop"<<endl;
        packetDrop = true;
        //setReselectionCounter(0);
        //setAllocatedBlocksPrevious(0);

    }
    else
    {
        packetDrop = false;
    }
*/

    for(int j=0;j<cResel;j++)
    {

        EV<<"Storing future message arrivals: "<<j*grant->getRri()<<endl;
        futureTransmissions.push_back(round((NOW.dbl()+j*0.1)*1000.0)/1000.0);
        grant->setGrantSubsequent(futureTransmissions);
    }



    // Send the packet up to the MAC layer where it will choose the CSR and the retransmission if that is specified
    // Need to generate the message that is to be sent to the upper layers.
    SPSResourcePool* candidateResourcesMessage = new SPSResourcePool("CSRs");
    candidateResourcesMessage->setCSRs(optimalCSRs);
    candidateResourcesMessage->setGrant(grant);
    LtePhyBase* phy=check_and_cast<LtePhyBase*>(getParentModule()->getSubmodule("phy"));
    phy->sendUpperPackets(candidateResourcesMessage);


}

std::vector<std::tuple<double, int, double>> SidelinkResourceAllocation::selectBestRSSIs(std::vector<double> subframes, LteSidelinkGrant* &grant, double subFrame)
{
    subch = new Subchannel(numSubchannels_,subFrame);
    EV << NOW << " LtePhyVUeMode4::selectBestRSSIs - Selecting best CSRs from possible CSRs..." << endl;
    int decrease = pStep_;
    if (grant->getPeriod() < 100)
    {
        // Same as pPrimeRsvpTx from other parts of the function
        decrease = (pStep_ * grant->getPeriod())/100;
    }

    int maxLatency = grant->getMaximumLatency();

    // Start and end of Selection Window.
    int minSelectionIndex = (10 * pStep_) + selectionWindowStartingSubframe_;
    int maxSelectionIndex = (10 * pStep_) + maxLatency;

    unsigned int grantLength = grant->getNumSubchannels();

    // This will be avgRSSI -> (subframeIndex, subchannelIndex)
    std::vector<std::tuple<double, int, double>> orderedCSRs;

    LtePhyBase* phy=check_and_cast<LtePhyBase*>(getParentModule()->getSubmodule("phy"));
    std::vector<std::pair<Band,double>> rssiD2DPeers=phy->getRSSIVector();

    EV<<"RSSI vector size: "<<rssiD2DPeers.size()<<endl;
    double averageRSSI = 0.0;
    for(int k=0; k<rssiD2DPeers.size();k++)
    {
        averageRSSI=0.0;

    }

    double averageRSSIPeers =averageRSSI/rssiD2DPeers.size();

    orderedCSRs.emplace_back(averageRSSIPeers, 9, subFrame);
    // Shuffle ensures that the subframes and subchannels appear in a random order, making the selections more balanced
    // throughout the selection window.
    std::random_shuffle (orderedCSRs.begin(), orderedCSRs.end());

    /* std::sort(begin(orderedCSRs), end(orderedCSRs), [](const std::tuple<double, int, int> &t1, const std::tuple<double, int, int> &t2) {
            return get<0>(t1) < get<0>(t2); // or use a custom compare function
        });*/

    int minSize = std::round(totalPossibleCSRs * .2);
    orderedCSRs.resize(minSize);

    return orderedCSRs;
}

void SidelinkResourceAllocation::storeAirFrame(LteAirFrame* frame, UserControlInfo* lteInfo)
{
    // implements the capture effect
    // store the frame received from the nearest transmitter

    /*EV<<""<<endl;
    // Need to be able to figure out which subchannel is associated to the Rbs in this case
    if (lteInfo->getFrameType() == SCIPKT){
        sciFrames_.push_back(frame);
    }
    else{
        tbFrames_.push_back(frame);
    }

    decodeAirFrame(frame,lteInfo);*/
}

void SidelinkResourceAllocation::decodeAirFrame(LteAirFrame* frame, UserControlInfo* lteInfo)
{
    EV << NOW << " SidelinkResourceAllocation::decodeAirFrame - Start decoding..." << endl;


}

std::tuple<int,int> SidelinkResourceAllocation::decodeRivValue(SidelinkControlInformation* sci, UserControlInfo* sciInfo)
{
    EV << NOW << " SidelinkResourceAllocation::decodeRivValue - Decoding RIV value of SCI allows correct placement in sensing window..." << endl;
    int subchannelIndex = 0;
    int lengthInSubchannels = numSubchannels_;
    return std::make_tuple(subchannelIndex, lengthInSubchannels);
}

//Keeps a track of measured RSSI in every subframe
void  SidelinkResourceAllocation::initialiseSensingWindow()
{
    Enter_Method("initialiseSensingWindow()");

    //EV << NOW << " SidelinkResourceAllocation::initialiseSensingWindow in each subframe" << endl;
    txStatus = false;
    rxStatus=false;
    rssiReception= 0.0;
    rsrpReception=0.0;
    subframeTime = NOW;
    sensingWindow.set_capacity(1000);  //Limit buffer capacity to 1000

    sensingWindow.push_back(std::make_tuple(subframeTime.dbl(),rssiReception,rsrpReception,txStatus,rxStatus));

    //Iterate through circular buffer and also the tuple

    //EV<<"Sensing window size: "<<sensingWindow.size()<<endl;

    //To verify
    /*    for (auto [X, Y,Z,A,B]:sensingWindow)
    {
        EV<<"Sensing window parameters: "<<X<<" "<<Y<<" "<<Z<<" "<<A<<" "<<B<<endl;
    }*/
}

// Updating sensing window when packet is transmitted or received
boost::circular_buffer<std::tuple<double, double,double,bool,bool>> SidelinkResourceAllocation::updateSensingWindow(double subframeTime, double rssi, double rsrp, bool txStatus, bool rxStatus)
{
    EV<<"Updating Sensing window for subframe: "<<subframeTime<< "on transmitting: "<<txStatus<<"on receiving: "<<rxStatus<<endl;
    sensingWindow.set_capacity(1000);  //Limit buffer capacity to 1000
    //Sensing window was initialized with some values. Now we replace with current values when packet is transmitted or received.

    /*for (auto [X, Y,Z,A,B]:sensingWindow)
    {
        EV<<"Sensing window current: "<<X<<" "<<Y<<" "<<Z<<" "<<A<<" "<<B<<endl;
    }*/

    //EV<<"Sensing window size: "<<sensingWindow.size();
    auto itc=sensingWindow.begin();

    for (;itc != sensingWindow.end();++itc) {
        if(get<0>(*itc)==subframeTime)
        {
            //Replace the values on transmission or reception
            sensingWindow.erase(itc);
            sensingWindow.push_back(std::make_tuple(subframeTime,rssi,rsrp,txStatus,rxStatus));

        }
    }

    //sensingWindow.push_back(std::make_tuple(subframeTime,rssi,rsrp,txStatus,rxStatus));

/*    for (auto [X, Y,Z,A,B]:sensingWindow)
    {
        //EV<<"Sensing window updated parameters: "<<X<<" "<<Y<<" "<<Z<<" "<<A<<" "<<B<<endl;
    }*/
    setSensingWindow(sensingWindow); //Used by computeCSRs() method
    return sensingWindow;
}

simtime_t SidelinkResourceAllocation::sidelinkSynchronization(bool status)
{
    Enter_Method("sidelinkSynchronization()");
    //Synchronization messages are scheduled every 160ms
    //EV<<"Synchronization subframes"<<endl;
    slsync = new  cMessage("SLSS");

    SidelinkSynchronization* slss = new SidelinkSynchronization("SLSS");
    LteAirFrame* frame = new LteAirFrame("SLSS");
    UserControlInfo* lteInfo = new UserControlInfo ();
    frame->encapsulate(check_and_cast<cPacket*>(slss));
    lteInfo->setFrameType(SYNC);
    lteInfo->setDirection(D2D_MULTI);
    frame->setControlInfo(lteInfo);
    slsync->setSchedulingPriority(0);


    nextSLSS = (NOW+80*TTI);
    scheduleAt(NOW+80*TTI, slsync);

    LtePhyBase* phy=check_and_cast<LtePhyBase*>(getParentModule()->getSubmodule("phy"));
    phy->sendBroadcast(frame);
    return nextSLSS;
}


//Congestion control parameters
void SidelinkResourceAllocation::initialiseFreqAllocationMap()
{
    freqAllocationMap.set_capacity(1000);
    EV<<"SidelinkResourceAllocation::initialiseFreqAllocationMap"<<endl;
    //  freqAllocationMap.push_back(std::make_tuple(NOW.dbl(), 0.0));
}

boost::circular_buffer<std::tuple<double, int>> SidelinkResourceAllocation::updateFreqAllocationMap(double subframeTime, int allocatedRB )
{
    EV<<"SidelinkResourceAllocation::updateFreqAllocationMap"<<endl;
    //auto itf=freqAllocationMap.begin();
    freqAllocationMap.set_capacity(1000);
    freqAllocationMap.push_back(std::make_tuple(subframeTime, allocatedRB));

    /*    for (;itf != freqAllocationMap.end();++itf) {
        if(get<0>(*itf)==subframeTime)
        {
            //Replace the values on transmission or reception
            freqAllocationMap.erase(itf);
            //throw cRuntimeError("SidelinkResourceAllocation::updateFreqAllocationMap ");
            freqAllocationMap.push_back(std::make_tuple(subframeTime, allocatedRB));
        }
        setFreqAllocationMap(freqAllocationMap);


    }*/


    //View updated Frequency allocation map
    /*   for (auto [X, Y]:freqAllocationMap)
    {
        EV<<"Frequency allocation map for transmissions: "<<X<<" "<<Y<<endl;
    }*/
    return freqAllocationMap;
}

void  SidelinkResourceAllocation::initialiseCbrWindow()
{
    Enter_Method("initialiseCbrWindow()");

    //EV << NOW << " SidelinkResourceAllocation::initialiseCbrWindow in each subframe" << endl;
    txStatus = false;
    rxStatus=false;
    rssiReception= 0.0;
    rsrpReception=0.0;
    subframeTime = NOW;
    cbrWindow.set_capacity(100);  //Limit buffer capacity to 1000
    occupiedResourceBlocks = RBIndicesSCI.size()+RBIndicesData.size();
    calculateChannelBusyRatio(occupiedResourceBlocks);

    cbrWindow.push_back(std::make_tuple(subframeTime.dbl(),calculateChannelBusyRatio(occupiedResourceBlocks)));

    //Iterate through circular buffer and also the tuple

    EV<<"CBR window size: "<<cbrWindow.size()<<endl;

    //To verify
    /*for (auto [X, Y]:cbrWindow)
    {
        EV<<"CBR window initialized: "<<X<<" "<<Y<<endl;
    }*/
}

boost::circular_buffer<std::tuple<double,double>>  SidelinkResourceAllocation::updateCbrWindow(double subframeTime,double cbr)

{
    cbrWindow.set_capacity(100);  //Limit buffer capacity to 1000
    //Sensing window was initialized with some values. Now we replace with current values when packet is transmitted or received.

    /*for (auto [X, Y]:cbrWindow)
    {
        EV<<"CBR window current: "<<X<<" "<<Y<<endl;
    }*/

    EV<<"CBR window size: "<<cbrWindow.size();
    auto itc=cbrWindow.begin();

    for (;itc != cbrWindow.end();++itc) {
        if(get<0>(*itc)==subframeTime)
        {
            //Replace the values on transmission or reception
            cbrWindow.erase(itc);
            cbrWindow.push_back(std::make_tuple(subframeTime,cbr));

        }
    }

    //sensingWindow.push_back(std::make_tuple(subframeTime,rssi,rsrp,txStatus,rxStatus));

    /*for (auto [X, Y]:cbrWindow)
    {
        EV<<"CBR window updated parameters: "<<X<<" "<<Y<<endl;
    }*/
    setCbrWindow(cbrWindow);
    return cbrWindow;
}




double SidelinkResourceAllocation::calculateChannelBusyRatio(int occupiedRB)
{
    if(occupiedRB>0)
    {
        cbr = occupiedRB/(numSubchannels_ *subchannelSize_) ;
    }
    else
    {
        EV<<"CBR regulation"<<endl;
        cbr = 0.1;
    }

    return cbr;
}

//Calculate channel occupancy ratio
double SidelinkResourceAllocation::calculateChannelOccupancyRatio(boost::circular_buffer<std::tuple<double, int>> freqallocmap,int cresel)
{
    EV<<"SidelinkResourceAllocation::calculateChannelOccupancyRatio: "<<endl;

    //Calculated for the transmitter - both past and future transmissions

    int sum = 0;

    //double futureAllocationTime = NOW.dbl()+(cresel-1)*0.1;

    //Past allocations are stored in freqAllocationMap. For future allocations, we determine based on CResel.
    boost::circular_buffer<std::tuple<double, int>>::iterator itc = freqallocmap.begin();
    double subframeTime = NOW.dbl();
    for (auto [X, Y]:freqallocmap)
    {

        if ((subframeTime-X)<=0.5 && subframeTime>X)
        {
            sum+=Y;
        }
    }

    //throw cRuntimeError("SRA");
    int b = std::get<1> (*(itc+(freqallocmap.size()-1)));


    sum = sum+b*(cresel-1);
    cr = sum/(1000.0*50.0);

    EV<<"Channel occupancy ratio (CR): "<<cr<<endl;
    return cr;
}




//Before transmission, based on CBR of previous 100 subframes, we check if the CR limit is reached
bool SidelinkResourceAllocation::checkCRLimit(double averageCbR, double crMeasured)
{
    //Average CBR over previous 100 subframes is considered
    EV<<"Average CBR: "<<averageCbr<<endl;

    if (0.65<averageCbR<0.8)
    {
        crLimit=0.02;

    }
    else if(0.8<averageCbR<1)
    {
        crLimit=0.01;

    }
    else
    {
        crLimit=0.0;
    }

    if (crMeasured<crLimit)
    {
        crLimitReached=true;
    }
    else
    {
        crLimitReached=false;
    }
    return crLimitReached;
}

void SidelinkResourceAllocation::finish()
{



}



