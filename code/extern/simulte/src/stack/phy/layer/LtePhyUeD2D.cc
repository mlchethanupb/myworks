#include <assert.h>
#include "stack/phy/layer/LtePhyUeD2D.h"
#include "stack/phy/packet/LteFeedbackPkt.h"
#include "stack/d2dModeSelection/D2DModeSelectionBase.h"
#include "stack/mac/packet/SPSResourcePoolMode3.h"
#include "stack/phy/packet/SPSResourcePool.h"
#include "stack/mac/packet/LteMacPdu.h"
Define_Module(LtePhyUeD2D);

LtePhyUeD2D::LtePhyUeD2D()
{
    handoverStarter_ = NULL;
    handoverTrigger_ = NULL;
}

LtePhyUeD2D::~LtePhyUeD2D()
{
    SPSResourcePool* csrpkt = new SPSResourcePool("CSRs");
    delete csrpkt;
}

void LtePhyUeD2D::initialize(int stage)
{
    LtePhyUe::initialize(stage);
    if (stage == 0)
    {

        d2dTxPower_ = par("d2dTxPower");
        d2dMulticastEnableCaptureEffect_ = par("d2dMulticastCaptureEffect");
        d2dDecodingTimer_ = NULL;

    }
    frameSent = false;
}

void LtePhyUeD2D::handleSelfMessage(cMessage *msg)
{

    if (msg->isName("doModeSwitchAtHandover"))
    {
        // call mode selection module to check if DM connections are possible
        cModule* enb = getSimulation()->getModule(binder_->getOmnetId(masterId_));
        D2DModeSelectionBase *d2dModeSelection = check_and_cast<D2DModeSelectionBase*>(enb->getSubmodule("lteNic")->getSubmodule("d2dModeSelection"));
        d2dModeSelection->doModeSwitchAtHandover(nodeId_, true);

        delete msg;
    }
    else
        LtePhyUe::handleSelfMessage(msg);
}

// TODO: ***reorganize*** method
void LtePhyUeD2D::handleAirFrame(cMessage* msg)
{


    if(strcmp(msg->getName(), "RRCStateChange")== 0)
    {
        //throw cRuntimeError("RRC Enb");
        delete msg;
        return;
    }

    UserControlInfo* lteInfo = check_and_cast<UserControlInfo*>(msg->removeControlInfo());
    receivedPacket = false;
    EV<<"LtePhyUeD2D::handleAirFrame Received: "<<msg->getName()<<" from "<<msg->getSenderModule()<<endl;
    if (useBattery_)
    {
        //TODO BatteryAccess::drawCurrent(rxAmount_, 0);
    }

    connectedNodeId_ = masterId_;
    LteAirFrame* frame = check_and_cast<LteAirFrame*>(msg);


    EV << "LtePhyUeD2D: received new LteAirFrame with ID " << lteInfo->getFrameType() << " from channel" << "source Id: "<<lteInfo->getSourceId()<<
            "Destination Id: "<<nodeId_<<endl;

    int sourceId = binder_->getOmnetId(lteInfo->getSourceId());
    if(sourceId == 0 )
    {

        // source has left the simulation
        delete msg;
        return;
    }

    //Update coordinates of this user
    if (lteInfo->getFrameType() == HANDOVERPKT)
    {
        EV<<"Check for HANDOVERPKT "<<endl;
        // check if handover is already in process
        if (handoverTrigger_ != NULL && handoverTrigger_->isScheduled())
        {
            delete lteInfo;
            delete frame;
            return;
        }

        handoverHandler(frame, lteInfo);
        return;
    }

    if (lteInfo->getFrameType()==SCIPKT && lteInfo->getNodeType()==ENODEB)
    {
        EV<<"Received SCI configured by eNodeB in managed mode ..."<<endl;
        sciframe = frame;
        sciframe->setControlInfo(lteInfo);

        sciframe->setSchedulingPriority(airFramePriority_);
        sciframe->setDuration(TTI);
        return;
    }

    if (lteInfo->getFrameType() == SCIPKT)
    {
        EV<<"Received SCI from other vehicles ..."<<endl;
        //Process SCI
        decodeSci(frame, lteInfo);
        return;
    }
    if (lteInfo->getFrameType()==DATAPKT)
    {
        //Statistics collection


        EV<<"Received DATAPKT from: "<<lteInfo->getSourceId()<<endl;
        decodeAirFrame(frame, lteInfo);
        numAirFrameReceived_ = numAirFrameReceived_+1;
        emit(numberReceivedPackets,numAirFrameReceived_);
        EV<<"Sending received airframepdu to MAC layer"<<endl;
        cPacket* recvdpdu = check_and_cast<cPacket*>(frame->decapsulate());
        recvdpdu->setControlInfo(lteInfo);
        send (recvdpdu,upperGateOut_);

        return;

    }


    if(lteInfo->getFrameType()==CSRPKT)
    {

        SPSResourcePoolMode3* csr  = check_and_cast<SPSResourcePoolMode3*>(frame->decapsulate());

        csr->setControlInfo(lteInfo);
        EV<<"CSRPKT LtePhyUeD2D: "<<csr<<endl;
        send(csr, upperGateOut_);

        return;

    }


    // send H-ARQ feedback up
    if (lteInfo->getFrameType() == HARQPKT || lteInfo->getFrameType() == GRANTPKT || lteInfo->getFrameType() == RACPKT || lteInfo->getFrameType() == D2DMODESWITCHPKT)
    {
        handleControlMsg(frame, lteInfo);
        return;
    }



    if ((lteInfo->getUserTxParams()) != NULL)
    {
        int cw = lteInfo->getCw();
        if (lteInfo->getUserTxParams()->readCqiVector().size() == 1)
            cw = 0;
        double cqi = lteInfo->getUserTxParams()->readCqiVector()[cw];
        //if (lteInfo->getDirection() == DL)

    }

}

void LtePhyUeD2D::triggerHandover()
{
    // stop active D2D flows (go back to Infrastructure mode)
    // currently, DM is possible only for UEs served by the same cell

    // trigger D2D mode switch
    cModule* enb = getSimulation()->getModule(binder_->getOmnetId(masterId_));
    D2DModeSelectionBase *d2dModeSelection = check_and_cast<D2DModeSelectionBase*>(enb->getSubmodule("lteNic")->getSubmodule("d2dModeSelection"));
    d2dModeSelection->doModeSwitchAtHandover(nodeId_, false);

    LtePhyUe::triggerHandover();
}

void LtePhyUeD2D::doHandover()
{
    // amc calls
    LteAmc *oldAmc = getAmcModule(masterId_);
    LteAmc *newAmc = getAmcModule(candidateMasterId_);
    assert(newAmc != NULL);
    oldAmc->detachUser(nodeId_, D2D);
    newAmc->attachUser(nodeId_, D2D);

    LtePhyUe::doHandover();

    // send a self-message to schedule the possible mode switch at the end of the TTI (after all UEs have performed the handover)
    cMessage* msg = new cMessage("doModeSwitchAtHandover");
    msg->setSchedulingPriority(10);
    scheduleAt(NOW, msg);
}

void LtePhyUeD2D::handleUpperMessage(cMessage* msg)
{

    if(strcmp(msg->getName(), "RRCStateChange")== 0)
    {
        RRCStateChange* rrcstate = check_and_cast<RRCStateChange*> (msg);
        rrcCurrentState = rrcstate->getState();
        EV<<"RRC state PHY: "<<rrcCurrentState<<endl;
        return;
    }

    if(strcmp(msg->getName(), "LteMode3Grant")== 0)
    {
        enb = new LtePhyEnbD2D();
        enb->handleUpperMessage(msg);
    }

    if(strcmp(msg->getName(), "LteMode4Grant")== 0)

    {
        LteSidelinkGrant* grant = check_and_cast<LteSidelinkGrant*>(msg);
        SidelinkResourceAllocation* sra = check_and_cast<SidelinkResourceAllocation*>(getParentModule()->getSubmodule("mode4"));
        EV<<"SCI configured in unmanaged mode ..."<<endl;
        sciframe = sra->createSCIMessage(msg,grant);

        EV<<"LtePhyUeD2D::handleUpperMessage received sidelink grant"<<grant->getTransmitBlockSize()<<endl;
        sra->handleUpperMessage(grant);

        //SCI
        sciframe->setSchedulingPriority(airFramePriority_);
        sciframe->setDuration(TTI);

        return;
    }
    if (strcmp(msg->getName(), "CSRsPrevious")==0)
    {
        SPSResourcePool* grantedblocksprevious = check_and_cast<SPSResourcePool *>(msg);
        SidelinkResourceAllocation* sra = check_and_cast<SidelinkResourceAllocation*>(getParentModule()->getSubmodule("mode4"));
        sra->setAllocatedBlocksPrevious(grantedblocksprevious->getAllocatedBlocksScIandDataPrevious());
        EV<<"Allocated blocks previous: "<<grantedblocksprevious->getAllocatedBlocksScIandDataPrevious()<<endl;
        return;
    }


    UserControlInfo* lteInfo = check_and_cast<UserControlInfo*>(msg->removeControlInfo());
    if(lteInfo->getIpBased()==true)
    {
        EV<<"Check for IPBased: "<<lteInfo->getIpBased()<< "Transmitting packet ID: "<<lteInfo->getPktId()<<endl;
        numAirFrameAlertTransmitted_ = numAirFrameAlertTransmitted_ +1;
        emit(numberAlertTransmittedPackets,numAirFrameAlertTransmitted_ );  //Number of packets sent across the radio interface
        emit(AlertTrPktId,lteInfo->getPktId());

    }



    if ((lteInfo->getFrameType()==MODE3GRANTREQUEST))
    {
        frame = new LteAirFrame("Mode3GrantRequest");
        lteInfo->setSourceId(nodeId_);
        lteInfo->setDestId(candidateMasterId_);
        frame->encapsulate(check_and_cast<cPacket*>(msg));
        frame->setDuration(TTI);
        frame->setControlInfo(lteInfo);

        OmnetId destOmnetId = binder_->getOmnetId(candidateMasterId_);

        EV<<"Sending mode 3 grant request to eNodeB"<<endl;
        sendUnicast(frame);
        return;
    }

    if ((lteInfo->getFrameType()==DATAARRIVAL))
    {
        frame = new LteAirFrame("Data Arrival");
        lteInfo->setSourceId(nodeId_);
        lteInfo->setDestId(candidateMasterId_);
        frame->encapsulate(check_and_cast<cPacket*>(msg));
        frame->setDuration(TTI);
        frame->setControlInfo(lteInfo);

        OmnetId destOmnetId = binder_->getOmnetId(candidateMasterId_);
        EV<<"Frame length: "<<frame->getBitLength()<<endl;

        EV<<"Inform eNodeB about newDataPkt"<<endl;

        sendUnicast(frame);

        return;
    }

    if (lteInfo->getFrameType() == HARQPKT || lteInfo->getFrameType() == GRANTPKT || lteInfo->getFrameType() == RACPKT)
    {
        frame = new LteAirFrame("harqFeedback-grant");

    }

    EV<<"Broadcasting sidelink control information (SCI)"<<endl;



    //Prepare data frame for broadcast
    EV<<"Prepare LteAirFrame for the message: "<<msg->getName()<<endl; //LteMacPdu
    frame = new LteAirFrame("airframePdu");
    frame->encapsulate(check_and_cast<cPacket*>(msg));
    LteRealisticChannelModel* chan = check_and_cast< LteRealisticChannelModel*>(getParentModule()->getSubmodule("channelModel"));


    setRSSIVector(rssiVector);

    // initialize frame fields

    frame->setSchedulingPriority(airFramePriority_);
    frame->setDuration(TTI);
    // set current position
    lteInfo->setCoord(getRadioPosition());
    lteInfo->setTxPower(txPower_);
    lteInfo->setD2dTxPower(d2dTxPower_);
    frame->setControlInfo(lteInfo);


    sendMulticast(sciframe);
    sendMulticast(frame);


    frameSent=true;
    SidelinkResourceAllocation* sra = check_and_cast<SidelinkResourceAllocation*>(getParentModule()->getSubmodule("mode4"));
    sra->updateSensingWindow(NOW.dbl(),rsrpMean,rssiMean, frameSent,false);
    //Decrement the re-selection counter on successful data frame transmission in mode 4

    if (frameSent==true && rrcCurrentState=="RRC_IDLE")
    {
        SidelinkResourceAllocation* sra = check_and_cast<SidelinkResourceAllocation*>(getParentModule()->getSubmodule("mode4"));
        cResel = sra->getReselectionCounter();
        cResel = cResel-1;
        sra->setReselectionCounter(cResel);
        EV<<"Successful transmission of TB, cResel: "<<sra->getReselectionCounter()<<endl;
        frameSent=false;

        if (cResel <=0)
        {
            cResel=0;
            sra->setReselectionCounter(cResel);
        }
        numAirFrameTransmitted_ = numAirFrameTransmitted_+1;
        emit(numberTransmittedPackets,numAirFrameTransmitted_);
        // emit(CAMPktId, lteInfo->getCAMId());//Packet IDs of successfully transmitted CAMs
        // EV<<"Check for CAMs: "<<lteInfo->getIpBased()<< "Transmitting CAM ID: "<<lteInfo->getCAMId()<<endl;
    }

    if (frameSent == true && (rrcCurrentState=="RRC_CONN" ||rrcCurrentState=="RRC_INACTIVE"))
    {
        EV<<"Notify eNodeB of successful transmission of TB"<<endl;
        numAirFrameTransmitted_ = numAirFrameTransmitted_+1;
        TxStatus* status = new TxStatus("Transmission");
        status->setNumberTransmissions( numAirFrameTransmitted_ );
        UserControlInfo* suinfo = new UserControlInfo();
        frame = new LteAirFrame("Transmission");
        frame->encapsulate(check_and_cast<cPacket*>(status));
        suinfo->setSourceId(nodeId_);
        suinfo->setDestId(candidateMasterId_);
        suinfo->setFrameType(TXSTATUS);
        frame->setControlInfo(suinfo);
        sendUnicast(frame);
        //throw cRuntimeError("status report");

    }

    //Number of CAMS successfully transmitted

    //numAirFrameTransmitted_ = numAirFrameTransmitted_+1;
    //emit(numberTransmittedPackets,numAirFrameTransmitted_);  //Number of packets sent across the radio interface


    //Number of Alert messages successfully transmitted

    /*numAirFrameAlertTransmitted_ = numAirFrameAlertTransmitted_ +1;
    emit(numberAlertTransmittedPackets,numAirFrameAlertTransmitted_ );  //Number of packets sent across the radio interface*/


}




void LtePhyUeD2D::decodeSci(LteAirFrame* frame, UserControlInfo* lteInfo)
{

    EV<<"DEcoding SCI received from broadcast by other vehicles ... "<<endl;
    SidelinkControlInformation* sci = check_and_cast<SidelinkControlInformation*> (frame->decapsulate());
    EV<<"CResel: "<<sci->getCResel()<<endl;
    numSubsequentReceptions = sci->getCResel()-1;

    //Reserve expected future receptions
    /* for (int j =1;j<sci->getCResel();j++){
        reserveSubframesReception.push_back(std::make_tuple(j*NOW.dbl()));
    }
     */
}


void LtePhyUeD2D::decodeAirFrame(LteAirFrame* frame, UserControlInfo* lteInfo)
{
    rssiVector.clear();
    rsrpVector.clear();
    EV << NOW << " LtePhyUeD2D::decodeAirFrame - Start decoding..." << endl;
    EV<<"Number of bytes received: "<<frame->getByteLength();
    LteRealisticChannelModel* chan = check_and_cast< LteRealisticChannelModel*>(getParentModule()->getSubmodule("channelModel"));
    rssiVector=chan->getRSSI(frame, lteInfo, lteInfo->getSourceId(), lteInfo->getCoord() , 0);
    rsrpVector = chan->getRSRP_D2D(lteInfo,rssiVector );

    //Compute mean RSSI and mean RSRP across LTE bands and use it for CSR calculation
    rsrpMean=0.0;
    rssiMean=0.0;

    for (int i = 0; i < rsrpVector.size(); i++)
    {
        rsrpMean += rsrpVector[i];
    }

    rsrpMean = rsrpMean / 6;
    setRsrpMean(rsrpMean);


    // std::vector<std::pair<Band,double>>::iterator iter;


    for(auto it:rssiVector)
    {       rssiMean+=it.second;
    }

    rssiMean=rssiMean/6;
    setRssiMean(rssiMean);

    EV<<"Mean RSRP: "<<  getRsrpMean()<<"Mean RSSI: "<<getRssiMean()<<endl;
    //Store mean RSRP,RSSI with timestamp of receiving frame
    phyMeasurements.push_back(std::make_tuple(frame->getArrivalTime().dbl(),rsrpMean,rssiMean));
    binder_->setMeasurements(phyMeasurements);
    SidelinkResourceAllocation* sra = check_and_cast<SidelinkResourceAllocation*>(getParentModule()->getSubmodule("mode4"));
    sra->updateSensingWindow(frame->getArrivalTime().dbl(),rsrpMean,rssiMean,false,true);

    //get number of allocated blocks
    int allocatedRB=20; //come back here
    sra->updateCbrWindow(frame->getArrivalTime().dbl(), sra->calculateChannelBusyRatio(10));

}






void LtePhyUeD2D::sendFeedback(LteFeedbackDoubleVector fbDl, LteFeedbackDoubleVector fbUl, FeedbackRequest req)
{
    Enter_Method("SendFeedback");
    EV << "LtePhyUeD2D: feedback from Feedback Generator" << endl;

    //Create a feedback packet
    LteFeedbackPkt* fbPkt = new LteFeedbackPkt();
    //Set the feedback
    fbPkt->setLteFeedbackDoubleVectorDl(fbDl);
    fbPkt->setLteFeedbackDoubleVectorDl(fbUl);
    fbPkt->setSourceNodeId(nodeId_);
    UserControlInfo* uinfo = new UserControlInfo();
    uinfo->setSourceId(nodeId_);
    uinfo->setDestId(masterId_);
    uinfo->setFrameType(FEEDBACKPKT);
    uinfo->setIsCorruptible(false);
    // create LteAirFrame and encapsulate a feedback packet
    LteAirFrame* frame = new LteAirFrame("feedback_pkt");
    frame->encapsulate(check_and_cast<cPacket*>(fbPkt));
    uinfo->feedbackReq = req;
    uinfo->setDirection(UL);
    simtime_t signalLength = TTI;
    uinfo->setTxPower(txPower_);
    uinfo->setD2dTxPower(d2dTxPower_);
    // initialize frame fields

    frame->setSchedulingPriority(airFramePriority_);
    frame->setDuration(signalLength);

    uinfo->setCoord(getRadioPosition());

    frame->setControlInfo(uinfo);
    //TODO access speed data Update channel index
    //    if (coherenceTime(move.getSpeed())<(NOW-lastFeedback_)){
    //        cellInfo_->channelIncrease(nodeId_);
    //        cellInfo_->lambdaIncrease(nodeId_,1);
    //    }
    lastFeedback_ = NOW;
    EV << "LtePhy: " << nodeTypeToA(nodeType_) << " with id "
            << nodeId_ << " sending feedback to the air channel" << endl;
    sendUnicast(frame);
}


void LtePhyUeD2D::finish()
{

    if (getSimulation()->getSimulationStage() != CTX_FINISH)
    {
        // do this only at deletion of the module during the simulation

        if (rrcCurrentState=="RRC_CONN")
            // amc calls
        {
            LteAmc *amc = getAmcModule(masterId_);

            if (amc != NULL)
                amc->detachUser(nodeId_, D2D);
            LtePhyUe::finish();
        }

    }
}
