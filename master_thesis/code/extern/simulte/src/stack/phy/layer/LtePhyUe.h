//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//

#ifndef _LTE_AIRPHYUE_H_
#define _LTE_AIRPHYUE_H_
#include <iterator>
#include "stack/phy/layer/LtePhyBase.h"
#include "stack/phy/das/DasFilter.h"
#include "stack/mac/layer/LteMacUe.h"
#include "stack/rlc/um/LteRlcUm.h"
#include "stack/phy/packet/SidelinkControlInformation_m.h"
#include "stack/phy/packet/SPSResourcePool.h"
#include "stack/mac/packet/LteSidelinkGrant.h"
#include "control/packet/SIB21.h"
#include "stack/phy/packet/SidelinkControlInformation_m.h"

#include "stack/mac/packet/LteSidelinkGrant.h"


class DasFilter;


class LtePhyUe : public LtePhyBase
{

protected:

    SidelinkResourceAllocation* mode4;
    LteMacUe *mac_;
    LteRlcUm *rlcUm_;

    cMessage *handoverStarter_;

    /** Self message to start the handover procedure */
    cMessage *handoverTrigger_;

    inet::Coord cellPos;
    double distanceFromEnb;
    std::string rrcCurrentState;
    /** Master MacNodeId */
    MacNodeId masterId_;
    MacNodeId  connectedNodeId_;



    /** RSSI received from the current serving node */
    double currentMasterRssi_;

    /** ID of not-master node from wich highest RSSI was received */
    MacNodeId candidateMasterId_;

    /** Highest RSSI received from not-master node */
    double candidateMasterRssi_;

    /**
     * Hysteresis threshold to evaluate handover: it introduces a small polarization to
     * avoid multiple subsequent handovers
     */
    double hysteresisTh_;

    /**
     * Value used to divide currentMasterRssi_ and create an hysteresisTh_
     * Use zero to have hysteresisTh_ == 0.
     */
    // TODO: bring it to ned par!
    double hysteresisFactor_;

    /**
     * Time interval elapsing from the reception of first handover broadcast message
     * to the beginning of handover procedure.
     * It must be a small number greater than 0 to ensure that all broadcast messages
     * are received before evaluating handover.
     * Note that broadcast messages for handover are always received at the very same time
     * (at bdcUpdateInterval_ seconds intervals).
     */
    // TODO: bring it to ned par!
    double handoverDelta_;

    // time for completion of the handover procedure
    double handoverLatency_;

    /**
     * Handover switch
     */
    bool enableHandover_;

    /**
     * Pointer to the DAS Filter: used to call das function
     * when receiving broadcasts and to retrieve physical
     * antenna properties on packet reception
     */
    DasFilter* das_;

    /// Threshold for antenna association
    // TODO: bring it to ned par!
    double dasRssiThreshold_;

    /** set to false if a battery is not present in module or must have infinite capacity */
    bool useBattery_;
    double txAmount_;    // drawn current amount for tx operations (mA)
    double rxAmount_;    // drawn current amount for rx operations (mA)
    //Sidelink related parameters

    int thresholdRSSI_;
    int commTxPoolNormalCommon;
    struct UsedRBs
    {
        simtime_t time_;
        RbMap rbMap_;
    };

    std::vector<UsedRBs> usedRbs_;

    simtime_t lastFeedback_;

    /** Statistic for serving cell */
    /** Self message to trigger handover procedure evaluation */


    virtual void initialize(int stage)override ;
    virtual void handleSelfMessage(cMessage *msg) override;
    virtual void handleAirFrame(cMessage* msg) override;
    virtual void finish() override;
    virtual void handleUpperMessage(cMessage* msg) override;

    /**
     * Catches host failure due to battery depletion.
     *
     * If the battery gets depleted, simpleBattery module publishes an HostState::FAILED
     * event to the blackboard. The event is caught by baseModule's receiveBBItem
     * which in turn calls handleHostState method, here inherited and redefined.
     */
    //virtual void handleHostState(const HostState& state);
    /**
     * Utility function to update the hysteresis threshold using hysteresisFactor_.
     */
    double updateHysteresisTh(double v);
    void handoverHandler(LteAirFrame* frame, UserControlInfo* lteInfo);
    void deleteOldBuffers(MacNodeId masterId);
    virtual void triggerHandover();
    virtual void doHandover();
    virtual void retrieveSIB21(cMessage *msg);
    void checkForDataTransmission();

public:
    LtePhyUe();
    virtual ~LtePhyUe();
    DasFilter *getDasFilter();
    /**
     * Send Feedback, called by feedback generator in DL
     */
    virtual void sendFeedback(LteFeedbackDoubleVector fbDl, LteFeedbackDoubleVector fbUl, FeedbackRequest req);
    MacNodeId getMasterId() const
    {
        return masterId_;
    }

    simtime_t coherenceTime(double speed)
    {
        double fd = (speed / SPEED_OF_LIGHT) * carrierFrequency_;
        return 0.1 / fd;
    }
    unsigned int getUsedRbs(const Remote antenna, Band b)
    {
        std::vector<UsedRBs>::iterator it = usedRbs_.begin();
        for (; it != usedRbs_.end(); ++it)
        {
            if (it->time_ == NOW)
                return it->rbMap_[antenna][b];
        }
    }
    unsigned int getPrevUsedRbs(const Remote antenna, Band b)
    {
        std::vector<UsedRBs>::iterator it = usedRbs_.begin();
        for (; it != usedRbs_.end(); ++it)
        {
            if (it->time_ == NOW-0.001)
                return it->rbMap_[antenna][b];
        }
        return 0;
    }


};

#endif  /* _LTE_AIRPHYUE_H_ */
