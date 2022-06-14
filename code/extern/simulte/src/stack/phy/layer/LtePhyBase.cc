//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//

#include "stack/phy/layer/LtePhyBase.h"
#include "common/LteCommon.h"

short LtePhyBase::airFramePriority_ = 10;

LtePhyBase::LtePhyBase()
{
    channelModel_ = NULL;
}

LtePhyBase::~LtePhyBase()
{
}

void LtePhyBase::initialize(int stage)
{
    ChannelAccess::initialize(stage);

    if (stage == inet::INITSTAGE_LOCAL)
    {
        binder_ = getBinder();
        cellInfo_ = NULL;
        // get gate ids
        upperGateIn_ = findGate("upperGateIn");
        upperGateOut_ = findGate("upperGateOut");
        radioInGate_ = findGate("radioIn");
        control_ = findGate("control");
        // Initialize and watch statistics
        numAirFrameReceived_ = numAirFrameNotReceived_ = 0;
        ueTxPower_ = par("ueTxPower");
        eNodeBtxPower_ = par("eNodeBTxPower");
        microTxPower_ = par("microTxPower");
        relayTxPower_ = par("relayTxPower");

        carrierFrequency_ = 2.1e+9;
        WATCH(numAirFrameReceived_);
        WATCH(numAirFrameNotReceived_);

        multicastD2DRange_ = par("multicastD2DRange");
        enableMulticastD2DRangeCheck_ = par("enableMulticastD2DRangeCheck");
    }
    else if (stage == inet::INITSTAGE_PHYSICAL_ENVIRONMENT_2)
    {
        initializeChannelModel();
    }
}

void LtePhyBase::handleMessage(cMessage* msg)
{
    EV << " LtePhyBase::handleMessage - new message received" <<  msg->getSenderModule()<<" "<<msg->getName()<<endl;

    if (msg->isSelfMessage())
    {
        EV<<"LtePhyBase:: handling the self message"<<endl;
        handleSelfMessage(msg);
        // throw cRuntimeError("LtePhyBase::handleMessage");
    }
    // AirFrame
    else if (msg->getArrivalGate()->getId() == radioInGate_)
    {
        EV<<"LtePhyBase::handleMessage: "<<msg->getName()<<endl;
        handleAirFrame(msg);
    }


    // message from stack
    else if (msg->getArrivalGate()->getId() == upperGateIn_)
    {
        EV<<"Sender Module 1: "<<msg->getSenderModule()<<endl;
        handleUpperMessage(msg);
    }
    else if (msg->isName("SIB21PreConfigured"))
    {
        EV<<"LtePhyBase::handleMessage SIB 21 message"<<endl;
        handleSelfMessage(msg);
    }

    // unknown message
    else
    {
        EV << "Unknown message received." << endl;

        delete msg;
    }
}

void LtePhyBase::handleControlMsg(LteAirFrame *frame,
        UserControlInfo *userInfo)
{
    EV<<"LtePhyBase::handleControlMsg"<<frame<<endl;

    cPacket *pkt = frame->decapsulate();
    EV<<"Sending pkt to MAC layer: "<<pkt->getName()<<endl;
    delete frame;
    pkt->setControlInfo(userInfo);

    EV<<"Sending pkt to MAC layer: "<<pkt->getName()<<endl;
    send(pkt, upperGateOut_);
    return;
}

LteAirFrame *LtePhyBase::createHandoverMessage()
{
    EV<<"LtePhyBase::createHandoverMessage"<<endl;
    // broadcast airframe
    LteAirFrame *bdcAirFrame = new LteAirFrame("handoverFrame");
    UserControlInfo *cInfo = new UserControlInfo();
    cInfo->setIsBroadcast(true);
    cInfo->setIsCorruptible(false);
    cInfo->setSourceId(nodeId_);
    cInfo->setFrameType(HANDOVERPKT);
    cInfo->setTxPower(txPower_);
    bdcAirFrame->setControlInfo(cInfo);

    bdcAirFrame->setDuration(0);
    bdcAirFrame->setSchedulingPriority(airFramePriority_);
    // current position
    cInfo->setCoord(getRadioPosition());
    return bdcAirFrame;
}

void LtePhyBase::handleUpperMessage(cMessage* msg)
{
    EV << "LtePhy: message from stack" << endl;

    UserControlInfo* lteInfo = check_and_cast<UserControlInfo*>(
            msg->removeControlInfo());

    LteAirFrame* frame = NULL;

    if (lteInfo->getFrameType() == HARQPKT
            || lteInfo->getFrameType() == GRANTPKT
            || lteInfo->getFrameType() == RACPKT
            || lteInfo->getFrameType() == D2DMODESWITCHPKT)
    {

        frame = new LteAirFrame("harqFeedback-grant");
    }
    else if (lteInfo->getFrameType()==SIDELINKGRANT){
        frame = new LteAirFrame("LTE sidelink-grant");
    }
    else
    {
        // create LteAirFrame and encapsulate the received packet
        frame = new LteAirFrame("airframe");
    }

    frame->encapsulate(check_and_cast<cPacket*>(msg));

    // initialize frame fields

    if (lteInfo->getFrameType() == D2DMODESWITCHPKT)
        frame->setSchedulingPriority(-1);
    else
        frame->setSchedulingPriority(airFramePriority_);
    frame->setDuration(TTI);
    // set current position
    lteInfo->setCoord(getRadioPosition());

    lteInfo->setTxPower(txPower_);
    frame->setControlInfo(lteInfo);

    EV << "LtePhy: " << nodeTypeToA(nodeType_) << " with id " << nodeId_
            << " sending message to the air channel. Dest=" << lteInfo->getDestId() << endl;
    sendUnicast(frame);
}

void LtePhyBase::initializeChannelModel()
{
    channelModel_ = check_and_cast<LteChannelModel*>(getParentModule()->getSubmodule("channelModel"));
    channelModel_->setBand(binder_->getNumBands());
    channelModel_->setPhy(this);
    return;
}

void LtePhyBase::updateDisplayString()
{
    char buf[80] = "";
    if (numAirFrameReceived_ > 0)
        sprintf(buf + strlen(buf), "af_ok:%d ", numAirFrameReceived_);
    if (numAirFrameNotReceived_ > 0)
        sprintf(buf + strlen(buf), "af_no:%d ", numAirFrameNotReceived_);
    getDisplayString().setTagArg("t", 0, buf);
}

void LtePhyBase::sendBroadcast(LteAirFrame *airFrame)
{
    // delegate the ChannelControl to send the airframe
    Enter_Method("LtePhyBase::sendBroadcast");

    sendToChannel(airFrame);
}

LteAmc *LtePhyBase::getAmcModule(MacNodeId id)
{
    LteAmc *amc = NULL;
    OmnetId omid = binder_->getOmnetId(id);
    if (omid == 0)
        return NULL;

    amc = check_and_cast<LteMacEnb *>(
            getSimulation()->getModule(omid)->getSubmodule("lteNic")->getSubmodule(
                    "mac"))->getAmc();
    return amc;
}

void LtePhyBase::sendMulticast(AirFrame *frame)
{

    //For the sake of implementation, we have edited this method for sidelink broadcast functionality
    // --! Do not confuse with definition of multicast

    UserControlInfo *ci = check_and_cast<UserControlInfo *>(frame->getControlInfo());

    EV<<"LtePhyBase::sendMulticast frame: "<<frame <<endl;

    //EV << NOW << " LtePhyBase::sendMulticast - node " << nodeIt->first << " is in the multicast group"<< endl;

    std::vector<inet::Coord> ueCoords;
    double distance;
    std::vector<UeInfo*>* ueList = binder_->getUeList();
    std::vector<UeInfo*>::iterator itue = ueList->begin();
    int k = 0;

    MacNodeId sourceId = nodeId_;
    LtePhyBase* phy = check_and_cast<LtePhyBase*>(getSimulation()->getModule(binder_->getOmnetId(sourceId))->getSubmodule("lteNic")->getSubmodule("phy"));
    inet::Coord sourceCoord = phy->getCoord();
    EV<<"Number of UEs in simulation: "<<ueList->size()<<endl;
    EV<<"Source UE Id : "<<sourceId<<" Source UE coordinates : "<<sourceCoord<<endl;
    if (ueList->size()!=0)
    {
        for (; itue != ueList->end(); ++itue)
        {
            MacNodeId UeId = (*itue)->id;
            LtePhyBase* phy = check_and_cast<LtePhyBase*>(getSimulation()->getModule(binder_->getOmnetId(UeId))->getSubmodule("lteNic")->getSubmodule("phy"));
            inet::Coord uePos = phy->getCoord();
            distance = uePos.distance(sourceCoord);
            //Saving the Info of broadcast neighbours
            if(UeId!=sourceId)
            {
                if((distance !=0 && distance<=500) && binder_->isNodeRegisteredInSimlation()==true)
                {
                    EV<<"Distance from ego vehicle: "<<distance<<endl;
                    binder_->BroadcastUeInfo[UeId]=uePos;
                    ueCoords.push_back(uePos);

                    //nonIpInfo->setBroadcastUeInfo(UeId,uePos);

                    k=k+1;
                }
                else
                {
                    EV<<"UEs outside sidelink broadcast range"<<endl;
                }
            }
        }
    }

        std::map<MacNodeId,inet::Coord>::iterator  nodeIt = binder_->BroadcastUeInfo.begin();
        EV<<"Sending to broadcast neighbours ..."<<binder_->BroadcastUeInfo.size()<<endl;
        for(; nodeIt != binder_->BroadcastUeInfo.end(); ++nodeIt)
        {

            cModule *receiver = getSimulation()->getModule(binder_->getOmnetId(nodeIt->first));
            EV << NOW << " LtePhyBase::sendMulticast - sending"<< frame <<" to node " << nodeIt->first << endl;
            EV<<"receiver module: "<<receiver<<endl;

            sendDirect(frame->dup(), 0, frame->getDuration(), receiver, getReceiverGateIndex(receiver));



        }

            // get a pointer to receiving module





        // delete the original frame
        EV<<"Frame: "<<frame<<endl;

        delete frame;
    }

    void LtePhyBase::sendUnicast(LteAirFrame *frame)
    {
        UserControlInfo *ci = check_and_cast<UserControlInfo *>(frame->getControlInfo());
        // dest MacNodeId from control info
        MacNodeId dest = ci->getDestId();
        // destination node (UE, RELAY or ENODEB) omnet id
        try {
            binder_->getOmnetId(dest);
        } catch (std::out_of_range& e) {
            delete frame;
            return;         // make sure that nodes that left the simulation do not send
        }
        OmnetId destOmnetId = binder_->getOmnetId(dest);
        if (destOmnetId == 0){
            // destination node has left the simulation
            delete frame;
            return;
        }
        // get a pointer to receiving module
        cModule *receiver = getSimulation()->getModule(destOmnetId);
        // receiver's gate
        sendDirect(frame, 0, frame->getDuration(), receiver, getReceiverGateIndex(receiver));

        return;
    }

    void LtePhyBase::sendUpperPackets(cMessage* msg)
    {
        // Send message
        send(msg,upperGateOut_);

    }

    int LtePhyBase::getReceiverGateIndex(const omnetpp::cModule *receiver) const
    {
        int gate = receiver->findGate("radioIn");

        if (gate < 0) {
            gate = receiver->findGate("lteRadioIn");
            if (gate < 0) {
                throw cRuntimeError("receiver \"%s\" has no suitable radio input gate",
                        receiver->getFullPath().c_str());
            }
        }
        return gate;
    }

    void LtePhyBase::deleteModule(){
        cancelAndDelete(ttiTick_);
        cSimpleModule::deleteModule();
    }







