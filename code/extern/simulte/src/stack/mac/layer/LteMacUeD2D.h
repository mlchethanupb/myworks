//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//

#ifndef _LTE_LTEMACUED2D_H_
#define _LTE_LTEMACUED2D_H_

#include "stack/mac/layer/LteMacUe.h"
#include "stack/mac/layer/LteMacEnbD2D.h"
#include "stack/mac/buffer/harq_d2d/LteHarqBufferTxD2D.h"
#include "stack/mac/configuration/SidelinkConfiguration.h"
#include "stack/mac/packet/LteSidelinkGrant.h"
#include "control/packet/RRCStateChange_m.h"
#include <iostream>
#include <cstring>
#include "common/LteCommon.h"
#include "stack/mac/scheduler/LteSchedulerUeSl.h"
#include "stack/mac/packet/DataArrival.h"
#include "stack/phy/layer/LtePhyBase.h"



class LteSchedulingGrant;
class LteSchedulerUeUl;
class LteSchedulerUeSl;
class LteBinder;
class SidelinkConfiguration;
class LteMacEnbD2D;
class LteMacUeD2D : public LteMacUe
{
    // reference to the eNB
    LteMacEnbD2D* enbmac_;
    SidelinkConfiguration* slConfig;
    LteSidelinkGrant* slGrant;
    UserTxParams* preconfiguredTxParams_;
    UserTxParams* getPreconfiguredTxParams();  // build and return new user tx params
    LteSchedulerUeSl* lteSchedulerUeSl_;
    ScheduleList* scheduleListSl_;
    double grantExpirationTime;
    // RAC Handling variables
    bool racD2DMulticastRequested_;
    // Multicast D2D BSR handling
    bool bsrD2DMulticastTriggered_;
    // if true, use the preconfigured TX params for transmission, else use that signaled by the eNB
    bool usePreconfiguredTxParams_;
    int transmissionPid;
    int transmissionCAMId;
    std::string rrcCurrentState;
    simsignal_t rcvdD2DModeSwitchNotification_;
    bool dataArrivalStatus;
    std::vector<double> futureArrivals;
    double messageArrivalTime;
    int possibleDataSize;
    
    simsignal_t numberofFreeBytes;

protected:

    /**
     * Reads MAC parameters for ue and performs initialization.
     */
    virtual void initialize(int stage);

    /**
     * Analyze gate of incoming packet
     * and call proper handler
     */
    virtual void handleMessage(cMessage *msg);

    /**
     * Main loop
     */


    virtual void macHandleGrant(cPacket* pkt);

    /*
     * Checks RAC status
     */
    virtual void checkRAC();

    /*
     * Receives and handles RAC responses
     */
    virtual void macHandleRac(cPacket* pkt);

    void macHandleD2DModeSwitch(cPacket* pkt);

    virtual LteMacPdu* makeBsr(int size);

    /**
     * macPduMake() creates MAC PDUs (one for each CID)
     * by extracting SDUs from Real Mac Buffers according
     * to the Schedule List.
     * It sends them to H-ARQ (at the moment lower layer)
     *
     * On UE it also adds a BSR control element to the MAC PDU
     * containing the size of its buffer (for that CID)
     */

    virtual  void macPduMake(MacCid cid=0 );

    virtual void handleSelfMessage();
public:
    LteMacUeD2D();
    virtual ~LteMacUeD2D();
    LteSidelinkGrant* mode4Grant;
    LteSidelinkGrant* mode3Grant;

    virtual bool isD2DCapable()
    {
        return true;
    }


    virtual void triggerBsr(MacCid cid)
    {
        if (connDesc_[cid].getDirection() == D2D_MULTI)
            bsrD2DMulticastTriggered_ = true;
        else
            bsrTriggered_ = true;
    }
    virtual void doHandover(MacNodeId targetEnb);
    LteSidelinkGrant* getSchedulingGrant();
    void setSchedulingGrant(LteSidelinkGrant*);
    void finish();

    bool isDataArrivalStatus() {
        return dataArrivalStatus;
    }

    void setDataArrivalStatus(bool dataArrivalStatus) {
        this->dataArrivalStatus = dataArrivalStatus;
    }
};

#endif
