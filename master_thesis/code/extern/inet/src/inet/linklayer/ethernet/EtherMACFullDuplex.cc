//
// Copyright (C) 2006 Levente Meszaros
// Copyright (C) 2011 Zoltan Bojthe
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//

#include "inet/linklayer/ethernet/EtherMACFullDuplex.h"

#include "inet/common/queue/IPassiveQueue.h"
#include "inet/common/NotifierConsts.h"
#include "inet/linklayer/ethernet/EtherFrame.h"
#include "inet/networklayer/common/InterfaceEntry.h"

namespace inet {

// TODO: refactor using a statemachine that is present in a single function
// TODO: this helps understanding what interactions are there and how they affect the state

Define_Module(EtherMACFullDuplex);

EtherMACFullDuplex::EtherMACFullDuplex()
{
}

void EtherMACFullDuplex::initialize(int stage)
{
    EtherMACBase::initialize(stage);

    if (stage == INITSTAGE_LOCAL) {
        if (!par("duplexMode").boolValue())
            throw cRuntimeError("Half duplex operation is not supported by EtherMACFullDuplex, use the EtherMAC module for that! (Please enable csmacdSupport on EthernetInterface)");
    }
    else if (stage == INITSTAGE_LINK_LAYER) {
        beginSendFrames();    //FIXME choose an another stage for it
    }
}

void EtherMACFullDuplex::initializeStatistics()
{
    EtherMACBase::initializeStatistics();

    // initialize statistics
    totalSuccessfulRxTime = 0.0;
}

void EtherMACFullDuplex::initializeFlags()
{
    EtherMACBase::initializeFlags();

    duplexMode = true;
    physInGate->setDeliverOnReceptionStart(false);
}

void EtherMACFullDuplex::handleMessage(cMessage *msg)
{
    if (!isOperational) {
        handleMessageWhenDown(msg);
        return;
    }

    if (channelsDiffer)
        readChannelParameters(true);

    if (msg->isSelfMessage())
        handleSelfMessage(msg);
    else if (msg->getArrivalGate() == upperLayerInGate)
        processFrameFromUpperLayer(check_and_cast<EtherFrame *>(msg));
    else if (msg->getArrivalGate() == physInGate)
        processMsgFromNetwork(PK(msg));
    else
        throw cRuntimeError("Message received from unknown gate!");
}

void EtherMACFullDuplex::handleSelfMessage(cMessage *msg)
{
    EV_TRACE << "Self-message " << msg << " received\n";

    if (msg == endTxMsg)
        handleEndTxPeriod();
    else if (msg == endIFGMsg)
        handleEndIFGPeriod();
    else if (msg == endPauseMsg)
        handleEndPausePeriod();
    else
        throw cRuntimeError("Unknown self message received!");
}

void EtherMACFullDuplex::startFrameTransmission()
{
    ASSERT(curTxFrame);
    EV_DETAIL << "Transmitting a copy of frame " << curTxFrame << endl;

    EtherFrame *frame = curTxFrame->dup();    // note: we need to duplicate the frame because we emit a signal with it in endTxPeriod()
    if (frame->getSrc().isUnspecified())
        frame->setSrc(address);

    if (frame->getByteLength() < curEtherDescr->frameMinBytes)
        frame->setByteLength(curEtherDescr->frameMinBytes);     // extra padding

    // add preamble and SFD (Starting Frame Delimiter), then send out
    EtherPhyFrame *phyFrame = encapsulate(frame);

    // send
    EV_INFO << "Transmission of " << frame << " started.\n";
    send(phyFrame, physOutGate);

    scheduleAt(transmissionChannel->getTransmissionFinishTime(), endTxMsg);
    transmitState = TRANSMITTING_STATE;
    emit(transmitStateSignal, TRANSMITTING_STATE);
}

void EtherMACFullDuplex::processFrameFromUpperLayer(EtherFrame *frame)
{
    ASSERT(frame->getByteLength() >= MIN_ETHERNET_FRAME_BYTES);

    EV_INFO << "Received " << frame << " from upper layer." << endl;

    emit(packetReceivedFromUpperSignal, frame);

    if (frame->getDest().equals(address)) {
        throw cRuntimeError("logic error: frame %s from higher layer has local MAC address as dest (%s)",
                frame->getFullName(), frame->getDest().str().c_str());
    }

    if (frame->getByteLength() > MAX_ETHERNET_FRAME_BYTES) {    //FIXME two MAX FRAME BYTES in specif...
        throw cRuntimeError("packet from higher layer (%d bytes) exceeds maximum Ethernet frame size (%d)",
                (int)(frame->getByteLength()), MAX_ETHERNET_FRAME_BYTES);
    }

    if (!connected || disabled) {
        EV_WARN << (!connected ? "Interface is not connected" : "MAC is disabled") << " -- dropping packet " << frame << endl;
        emit(dropPkFromHLIfaceDownSignal, frame);
        numDroppedPkFromHLIfaceDown++;
        delete frame;

        requestNextFrameFromExtQueue();
        return;
    }

    // fill in src address if not set
    if (frame->getSrc().isUnspecified())
        frame->setSrc(address);

    bool isPauseFrame = (dynamic_cast<EtherPauseFrame *>(frame) != nullptr);

    if (!isPauseFrame) {
        numFramesFromHL++;
        emit(rxPkFromHLSignal, frame);
    }

    if (txQueue.extQueue) {
        ASSERT(curTxFrame == nullptr);
        ASSERT(transmitState == TX_IDLE_STATE || transmitState == PAUSE_STATE);
        curTxFrame = frame;
    }
    else {
        if (txQueue.innerQueue->isFull())
            throw cRuntimeError("txQueue length exceeds %d -- this is probably due to "
                                "a bogus app model generating excessive traffic "
                                "(or if this is normal, increase txQueueLimit!)",
                    txQueue.innerQueue->getQueueLimit());
        // store frame and possibly begin transmitting
        EV_DETAIL << "Frame " << frame << " arrived from higher layers, enqueueing\n";
        txQueue.innerQueue->insertFrame(frame);

        if (!curTxFrame && !txQueue.innerQueue->isEmpty() && transmitState == TX_IDLE_STATE)
            curTxFrame = (EtherFrame *)txQueue.innerQueue->pop();
    }

    if (transmitState == TX_IDLE_STATE)
        startFrameTransmission();
}

void EtherMACFullDuplex::processMsgFromNetwork(cPacket *pk)
{
    EtherTraffic *msg = check_and_cast<EtherTraffic *>(pk);

    EV_INFO << msg << " received." << endl;

    if (!connected || disabled) {
        EV_WARN << (!connected ? "Interface is not connected" : "MAC is disabled") << " -- dropping msg " << msg << endl;
        if (EtherPhyFrame *phyFrame = dynamic_cast<EtherPhyFrame *>(msg)) {    // do not count JAM and IFG packets
            EtherFrame *frame = decapsulate(phyFrame);
            emit(dropPkIfaceDownSignal, frame);
            delete frame;
            numDroppedIfaceDown++;
        }
        else
            delete msg;

        return;
    }

    EtherPhyFrame *phyFrame = dynamic_cast<EtherPhyFrame *>(msg);
    if (!phyFrame) {
        if (dynamic_cast<EtherFilledIFG *>(msg))
            throw cRuntimeError("There is no burst mode in full-duplex operation: EtherFilledIFG is unexpected");
        else
            throw cRuntimeError("Unexpected ethernet traffic: %s", msg->getClassName());
    }

    totalSuccessfulRxTime += phyFrame->getDuration();

    bool hasBitError = msg->hasBitError();

    EtherFrame *frame = decapsulate(phyFrame);
    emit(packetReceivedFromLowerSignal, frame);

    if (hasBitError) {
        numDroppedBitError++;
        emit(dropPkBitErrorSignal, frame);
        delete frame;
        return;
    }

    if (dropFrameNotForUs(frame))
        return;

    if (dynamic_cast<EtherPauseFrame *>(frame) != nullptr) {
        int pauseUnits = ((EtherPauseFrame *)frame)->getPauseTime();
        delete frame;
        numPauseFramesRcvd++;
        emit(rxPausePkUnitsSignal, pauseUnits);
        processPauseCommand(pauseUnits);
    }
    else {
        EV_INFO << "Reception of " << frame << " successfully completed." << endl;
        processReceivedDataFrame((EtherFrame *)frame);
    }
}

void EtherMACFullDuplex::handleEndIFGPeriod()
{
    ASSERT(nullptr == curTxFrame);
    if (transmitState != WAIT_IFG_STATE)
        throw cRuntimeError("Not in WAIT_IFG_STATE at the end of IFG period");

    // End of IFG period, okay to transmit
    EV_DETAIL << "IFG elapsed" << endl;

    getNextFrameFromQueue();
    beginSendFrames();
}

void EtherMACFullDuplex::handleEndTxPeriod()
{
    // we only get here if transmission has finished successfully
    if (transmitState != TRANSMITTING_STATE)
        throw cRuntimeError("End of transmission, and incorrect state detected");

    if (nullptr == curTxFrame)
        throw cRuntimeError("Frame under transmission cannot be found");

    emit(packetSentToLowerSignal, curTxFrame);    //consider: emit with start time of frame

    if (dynamic_cast<EtherPauseFrame *>(curTxFrame) != nullptr) {
        numPauseFramesSent++;
        emit(txPausePkUnitsSignal, ((EtherPauseFrame *)curTxFrame)->getPauseTime());
    }
    else {
        unsigned long curBytes = curTxFrame->getByteLength();
        numFramesSent++;
        numBytesSent += curBytes;
    }

    EV_INFO << "Transmission of " << curTxFrame << " successfully completed.\n";
    delete curTxFrame;
    curTxFrame = nullptr;
    lastTxFinishTime = simTime();


    if (pauseUnitsRequested > 0) {
        // if we received a PAUSE frame recently, go into PAUSE state
        EV_DETAIL << "Going to PAUSE mode for " << pauseUnitsRequested << " time units\n";

        scheduleEndPausePeriod(pauseUnitsRequested);
        pauseUnitsRequested = 0;
    }
    else {
        EV_DETAIL << "Start IFG period\n";
        scheduleEndIFGPeriod();
    }
}

void EtherMACFullDuplex::finish()
{
    EtherMACBase::finish();

    simtime_t t = simTime();
    simtime_t totalRxChannelIdleTime = t - totalSuccessfulRxTime;
    recordScalar("rx channel idle (%)", 100 * (totalRxChannelIdleTime / t));
    recordScalar("rx channel utilization (%)", 100 * (totalSuccessfulRxTime / t));
}

void EtherMACFullDuplex::handleEndPausePeriod()
{
    ASSERT(nullptr == curTxFrame);
    if (transmitState != PAUSE_STATE)
        throw cRuntimeError("End of PAUSE event occurred when not in PAUSE_STATE!");

    EV_DETAIL << "Pause finished, resuming transmissions\n";
    if (!curTxFrame)
        getNextFrameFromQueue();
    beginSendFrames();
}

void EtherMACFullDuplex::processReceivedDataFrame(EtherFrame *frame)
{
    // statistics
    unsigned long curBytes = frame->getByteLength();
    numFramesReceivedOK++;
    numBytesReceivedOK += curBytes;

    numFramesPassedToHL++;
    emit(packetSentToUpperSignal, frame);
    // pass up to upper layer
    EV_INFO << "Sending " << frame << " to upper layer.\n";
    send(frame, "upperLayerOut");
}

void EtherMACFullDuplex::processPauseCommand(int pauseUnits)
{
    if (transmitState == TX_IDLE_STATE) {
        EV_DETAIL << "PAUSE frame received, pausing for " << pauseUnitsRequested << " time units\n";
        if (pauseUnits > 0)
            scheduleEndPausePeriod(pauseUnits);
    }
    else if (transmitState == PAUSE_STATE) {
        EV_DETAIL << "PAUSE frame received, pausing for " << pauseUnitsRequested
                  << " more time units from now\n";
        cancelEvent(endPauseMsg);

        // Terminate PAUSE if pauseUnits == 0; Extend PAUSE if pauseUnits > 0
        scheduleEndPausePeriod(pauseUnits);
    }
    else {
        // transmitter busy -- wait until it finishes with current frame (endTx)
        // and then it'll go to PAUSE state
        EV_DETAIL << "PAUSE frame received, storing pause request\n";
        pauseUnitsRequested = pauseUnits;
    }
}

void EtherMACFullDuplex::scheduleEndIFGPeriod()
{
    ASSERT(nullptr == curTxFrame);
    transmitState = WAIT_IFG_STATE;
    emit(transmitStateSignal, WAIT_IFG_STATE);
    simtime_t endIFGTime = simTime() + (INTERFRAME_GAP_BITS / curEtherDescr->txrate);
    scheduleAt(endIFGTime, endIFGMsg);
}

void EtherMACFullDuplex::scheduleEndPausePeriod(int pauseUnits)
{
    ASSERT(nullptr == curTxFrame);
    // length is interpreted as 512-bit-time units
    simtime_t pausePeriod = ((pauseUnits * PAUSE_UNIT_BITS) / curEtherDescr->txrate);
    scheduleAt(simTime() + pausePeriod, endPauseMsg);
    transmitState = PAUSE_STATE;
    emit(transmitStateSignal, PAUSE_STATE);
}

void EtherMACFullDuplex::beginSendFrames()
{
    if (curTxFrame) {
        // Other frames are queued, transmit next frame
        EV_DETAIL << "Transmit next frame in output queue\n";
        startFrameTransmission();
    }
    else {
        // No more frames set transmitter to idle
        transmitState = TX_IDLE_STATE;
        emit(transmitStateSignal, TX_IDLE_STATE);
        if (!txQueue.extQueue) {
            // Output only for internal queue (we cannot be shure that there
            //are no other frames in external queue)
            EV_DETAIL << "No more frames to send, transmitter set to idle\n";
        }
    }
}

} // namespace inet

