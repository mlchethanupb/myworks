//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//


#include "stack/mac/layer/LteMacBase.h"
#include "stack/mac/buffer/harq/LteHarqBufferTx.h"
#include "stack/mac/buffer/harq_d2d/LteHarqBufferRxD2D.h"
#include "stack/mac/buffer/harq/LteHarqBufferRx.h"
#include "stack/mac/packet/LteMacPdu.h"
#include "stack/mac/buffer/LteMacQueue.h"
#include "common/LteControlInfo.h"
#include "corenetwork/binder/LteBinder.h"
#include "stack/mac/packet/LteHarqFeedback_m.h"
#include "stack/mac/buffer/LteMacBuffer.h"
#include "assert.h"

#include "../../../corenetwork/lteCellInfo/LteCellInfo.h"

LteMacBase::LteMacBase()
{
    mbuf_.clear();
    macBuffers_.clear();
}

LteMacBase::~LteMacBase()
{
    LteMacBuffers::iterator mit;
    LteMacBufferMap::iterator vit;
    for (mit = mbuf_.begin(); mit != mbuf_.end(); mit++)
        delete mit->second;
    for (vit = macBuffers_.begin(); vit != macBuffers_.end(); vit++)
        delete vit->second;
    mbuf_.clear();
    macBuffers_.clear();

    HarqTxBuffers::iterator htit;
    HarqRxBuffers::iterator hrit;
    for (htit = harqTxBuffers_.begin(); htit != harqTxBuffers_.end(); ++htit)
        delete htit->second;
    for (hrit = harqRxBuffers_.begin(); hrit != harqRxBuffers_.end(); ++hrit)
        delete hrit->second;
    harqTxBuffers_.clear();
    harqRxBuffers_.clear();
}

void LteMacBase::sendUpperPackets(cPacket* pkt)
{
    EV << "LteMacBase : Sending packet " << pkt->getName() << " on port MAC_to_RLC\n";
    // Send message
    send(pkt,up_[OUT]);
}

void LteMacBase::sendLowerPackets(cPacket* pkt)
{

    EV << "LteMacBase : Sending packet " << pkt->getName() << " on port MAC_to_PHY\n";


    // Send message
    updateUserTxParam(pkt);

    send(pkt,down_[OUT]);

}

void LteMacBase::sendPDULower(LteMacPdu* pdu)
{
    EV << "LteMacBase : Sending PDU " << pdu << " on port MAC_to_PHY\n";
    send(pdu,down_[OUT]);

}


/*
 * Upper layer handler
 */
void LteMacBase::fromRlc(cPacket *pkt)
{
    EV<<" LteMacBase::fromRlc"<<endl;
    handleUpperMessage(pkt);
}

/*
 * Lower layer handler
 */
void LteMacBase::fromPhy(cPacket *pkt)
{
    EV<<"LteMacBase::fromPhy"<<endl;
    // TODO: harq test (comment fromPhy: it has only to pass pdus to proper rx buffer and
    // to manage H-ARQ feedback)

    UserControlInfo *userInfo = check_and_cast<UserControlInfo *>(pkt->getControlInfo());
    MacNodeId src = userInfo->getSourceId();

    if (userInfo->getFrameType() == HARQPKT)
    {
        // H-ARQ feedback, send it to TX buffer of source
        HarqTxBuffers::iterator htit = harqTxBuffers_.find(src);
        EV << NOW << "Mac::fromPhy: node " << nodeId_ << " Received HARQ Feedback pkt" << endl;
        if (htit == harqTxBuffers_.end())
        {
            // if a feedback arrives, a tx buffer must exists (unless it is an handover scenario
            // where the harq buffer was deleted but a feedback was in transit)
            // this case must be taken care of

            if (binder_->hasUeHandoverTriggered(nodeId_) || binder_->hasUeHandoverTriggered(src))
                return;

            throw cRuntimeError("Mac::fromPhy(): Received feedback for an unexisting H-ARQ tx buffer");
        }
        LteHarqFeedback *hfbpkt = check_and_cast<LteHarqFeedback *>(pkt);
        htit->second->receiveHarqFeedback(hfbpkt);
    }
    else if (userInfo->getFrameType() == FEEDBACKPKT)
    {
        //Feedback pkt
        EV << NOW << "Mac::fromPhy: node " << nodeId_ << " Received feedback pkt" << endl;
        macHandleFeedbackPkt(pkt);
    }
    else if (userInfo->getFrameType()==GRANTPKT)
    {
        //Scheduling Grant
        EV << NOW << "Mac::fromPhy: node " << nodeId_ << " Received Scheduling Grant pkt" << endl;
        macHandleGrant(pkt);
    }
    else if(userInfo->getFrameType() == DATAPKT)
    {
        // data packet: insert in proper rx buffer
        EV << NOW << "Mac::fromPhy: node " << src << " Received DATA packet" << pkt->getByteLength()<<endl;
        //throw cRuntimeError("fromPHY");
        LteMacPdu *pdu = check_and_cast<LteMacPdu *>(pkt);
        Codeword cw = userInfo->getCw();
        /*EV<<"Codeword :"<<cw<<endl;
        HarqRxBuffers::iterator hrit = harqRxBuffers_.find(src);

        if (hrit != harqRxBuffers_.end())
        {
            EV<<"Inserting into HARQ RX Buffer"<<endl;
            hrit->second->insertPdu(cw,pdu);
        }
        else
        {
           // FIXME: possible memory leak
            EV<<"LteMacBase::fromPhy possible memory leak"<<endl;
            LteHarqBufferRx *hrb;
            if (userInfo->getDirection() == DL || userInfo->getDirection() == UL)
                hrb = new LteHarqBufferRx(ENB_RX_HARQ_PROCESSES, this,src);
            else // D2D
               // hrb = new LteHarqBufferRx(ENB_RX_HARQ_PROCESSES, this,src);
                 hrb = new LteHarqBufferRxD2D(ENB_RX_HARQ_PROCESSES, this,src, (userInfo->getDirection() == D2D_MULTI) );

            harqRxBuffers_[src] = hrb;

            hrb->insertPdu(cw,pdu);


        }*/
        macPduUnmake(pdu);

    }
    else if (userInfo->getFrameType() == RACPKT)
    {
        EV << NOW << "Mac::fromPhy: node " << nodeId_ << " Received RAC packet" << endl;
        macHandleRac(pkt);
    }

    else if (userInfo->getFrameType() == SCIPKT)
    {
        EV<<"LteMacBase receives SCIPKT"<<endl;
        throw cRuntimeError("LteMacBase::SCIPKT");
    }

    else if (userInfo->getFrameType()==MODE3GRANTREQUEST ||userInfo->getFrameType()==DATAARRIVAL)
    {
        fromPhy(pkt);
    }

    else if(userInfo->getFrameType() == CSRPKT)
    {
        throw cRuntimeError("CSRPKT MAC");
    }

    else
    {
        throw cRuntimeError("Unknown packet type %d", (int)userInfo->getFrameType());
    }
}

bool LteMacBase::bufferizePacket(cPacket* pkt)
{
    pkt->setTimestamp();        // Add timestamp with current time to packet
    EV<<"LteMacBase::bufferizePacket"<<endl;
    FlowControlInfo* lteInfo = check_and_cast<FlowControlInfo*>(pkt->getControlInfo());

    // obtain the cid from the packet informations
    MacCid cid = ctrlInfoToMacCid(lteInfo);

    // build the virtual packet corresponding to this incoming packet
    PacketInfo vpkt(pkt->getByteLength(), pkt->getTimestamp());

    LteMacBuffers::iterator it = mbuf_.find(cid);
    if (it == mbuf_.end())
    {
        // Queue not found for this cid: create
        LteMacQueue* queue = new LteMacQueue(queueSize_);
        take(queue);
        LteMacBuffer* vqueue = new LteMacBuffer();

        queue->pushBack(pkt);
        vqueue->pushBack(vpkt);
        mbuf_[cid] = queue;
        macBuffers_[cid] = vqueue;

        // make a copy of lte control info and store it to traffic descriptors map
        FlowControlInfo toStore(*lteInfo);
        connDesc_[cid] = toStore;
        // register connection to lcg map.
        LteTrafficClass tClass = (LteTrafficClass) lteInfo->getTraffic();

        lcgMap_.insert(LcgPair(tClass, CidBufferPair(cid, macBuffers_[cid])));

        EV << "LteMacBuffers 1 LteMacBase: Using new buffer on node: " <<
                MacCidToNodeId(cid) << " for Lcid: " << MacCidToLcid(cid) << ", Space left in the Queue: " <<
                queue->getQueueSize() - queue->getByteLength() << "\n";
    }
    else
    {
        // Found
        LteMacQueue* queue = it->second;
        LteMacBuffer* vqueue = macBuffers_.find(cid)->second;
        if (!queue->pushBack(pkt))
        {
            totalOverflowedBytes_ += pkt->getByteLength();
            double sample = (double)totalOverflowedBytes_ / (NOW - getSimulation()->getWarmupPeriod());
            if (lteInfo->getDirection()==DL)
            {
                emit(macBufferOverflowDl_,sample);
            }
            else if (lteInfo->getDirection()==UL)
            {
                emit(macBufferOverflowUl_,sample);
            }
            else // D2D
            {
                emit(macBufferOverflowD2D_,sample);
            }

            EV << "LteMacBuffers : Dropped packet: queue" << cid << " is full\n";
            delete pkt;
            return false;
        }
        vqueue->pushBack(vpkt);

        EV << "LteMacBuffers 2 LteMacBase : Using old buffer on node: " <<
                MacCidToNodeId(cid) << " for Lcid: " << MacCidToLcid(cid) << ", Space left in the Queue: " <<
                queue->getQueueSize() - queue->getByteLength() << "\n";
    }
    /// After bufferization buffers must be synchronized
    assert(mbuf_[cid]->getQueueLength() == macBuffers_[cid]->getQueueLength());
    return true;
}

void LteMacBase::deleteQueues(MacNodeId nodeId)
{
    EV<<"LteMacBase::deleteQueues"<<endl;
    LteMacBuffers::iterator mit;
    LteMacBufferMap::iterator vit;
    for (mit = mbuf_.begin(); mit != mbuf_.end(); )
    {
        if (MacCidToNodeId(mit->first) == nodeId)
        {
            while (!mit->second->isEmpty())
            {
                cPacket* pkt = mit->second->popFront();
                delete pkt;
            }
            delete mit->second;        // Delete Queue
            mbuf_.erase(mit++);        // Delete Elem
        }
        else
        {
            ++mit;
        }
    }
    for (vit = macBuffers_.begin(); vit != macBuffers_.end(); )
    {
        if (MacCidToNodeId(vit->first) == nodeId)
        {
            while (!vit->second->isEmpty())
                vit->second->popFront();
            delete vit->second;        // Delete Queue
            macBuffers_.erase(vit++);        // Delete Elem
        }
        else
        {
            ++vit;
        }
    }

    // delete H-ARQ buffers
    HarqTxBuffers::iterator hit;
    for (hit = harqTxBuffers_.begin(); hit != harqTxBuffers_.end(); )
    {
        if (hit->first == nodeId)
        {
            delete hit->second; // Delete Queue
            harqTxBuffers_.erase(hit++); // Delete Elem
        }
        else
        {
            ++hit;
        }
    }
    HarqRxBuffers::iterator hit2;
    for (hit2 = harqRxBuffers_.begin(); hit2 != harqRxBuffers_.end();)
    {
        if (hit2->first == nodeId)
        {
            delete hit2->second; // Delete Queue
            harqRxBuffers_.erase(hit2++); // Delete Elem
        }
        else
        {
            ++hit2;
        }
    }

    // TODO remove traffic descriptor and lcg entry
}


/*
 * Main functions
 */
void LteMacBase::initialize(int stage)
{
    if (stage == inet::INITSTAGE_LOCAL)
    {
        /* Gates initialization */
        up_[IN] = gate("RLC_to_MAC");
        up_[OUT] = gate("MAC_to_RLC");
        down_[IN] = gate("PHY_to_MAC");
        down_[OUT] = gate("MAC_to_PHY");
        control_IN = gate("control$i");
        control_OUT = gate("control$o");

        /* Create buffers */
        queueSize_ = par("queueSize");

        /* Get reference to binder */
        binder_ = getBinder();

        /* Set The MAC MIB */

        muMimo_ = par("muMimo");

        harqProcesses_ = par("harqProcesses");

        /* Start TTI tick */
        ttiTick_ = new cMessage("ttiTick_");
        ttiTick_->setSchedulingPriority(1);        // TTI TICK after other messages
        scheduleAt(NOW + TTI, ttiTick_);
        totalOverflowedBytes_ = 0;
        macBufferOverflowDl_ = registerSignal("macBufferOverFlowDl");
        macBufferOverflowUl_ = registerSignal("macBufferOverFlowUl");
        if (isD2DCapable())
            macBufferOverflowD2D_ = registerSignal("macBufferOverFlowD2D");

        measuredItbs_ = registerSignal("measuredItbs");
        WATCH(queueSize_);
        WATCH(nodeId_);
        WATCH_MAP(mbuf_);
        WATCH_MAP(macBuffers_);
    }
}

void LteMacBase::handleMessage(cMessage* msg)
{

    EV<<"LteMacBase::handleMessage Received message: "<<msg->getName()<<endl;


    if (msg->isSelfMessage())
    {
        handleSelfMessage();
        scheduleAt(NOW + TTI, ttiTick_);
        return;
    }

    cPacket* pkt = check_and_cast<cPacket *>(msg);
    EV << "LteMacBase : Received packet " << pkt->getName() <<
            " from port " << pkt->getArrivalGate()->getName() << endl;

    cGate* incoming = pkt->getArrivalGate();

    if (incoming == down_[IN])
    {
        // message from PHY_to_MAC gate (from lower layer)
        fromPhy(pkt);
    }
    else
    {
        // message from RLC_to_MAC gate (from upper layer)
        fromRlc(pkt);
    }
    return;
}





void LteMacBase::finish()
{
}

void LteMacBase::deleteModule(){
    cancelAndDelete(ttiTick_);
    cSimpleModule::deleteModule();
}

