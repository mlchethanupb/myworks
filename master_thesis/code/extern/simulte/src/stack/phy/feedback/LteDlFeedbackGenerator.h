//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//

#ifndef _LTE_LTEDLFBGENERATOR_H_
#define _LTE_LTEDLFBGENERATOR_H_

#include <omnetpp.h>

#include "../../../corenetwork/lteCellInfo/LteCellInfo.h"
#include "common/LteCommon.h"
#include "stack/phy/das/DasFilter.h"
#include "stack/phy/feedback/LteFeedback.h"
#include "common/timer/TTimer.h"
#include "common/timer/TTimerMsg_m.h"
#include "stack/phy/feedback/LteFeedbackComputation.h"
#include "corenetwork/binder/LteBinder.h"
class DasFilter;
/**
 * @class LteDlFeedbackGenerator
 * @brief Lte Downlink Feedback Generator
 *
 */
class LteDlFeedbackGenerator : public cSimpleModule
{
    enum FbTimerType
    {
        PERIODIC_SENSING = 0, PERIODIC_TX, APERIODIC_TX
    };

private:
    LteBinder* binder_;
    FeedbackType fbType_;               /// feedback type (ALLBANDS, PREFERRED, WIDEBAND)
    RbAllocationType rbAllocationType_; /// resource allocation type
    LteFeedbackComputation* lteFeedbackComputation_; // Object used to compute the feedback
    // Timers
    TTimer *tPeriodicSensing_;
    TTimer *tPeriodicTx_;
    TTimer *tAperiodicTx_;
    DasFilter *dasFilter_;  /// reference to das filter
    LteCellInfo *cellInfo_; /// reference to cellInfo
    FeedbackGeneratorType generatorType_;
    bool usePeriodic_;      /// true if we want to use also periodic feedback
    TxMode currentTxMode_;  /// transmission mode to use in feedback generation
    // cellInfo parameters
    std::map<Remote, int> antennaCws_; /// number of antenna per remote
    int numPreferredBands_;           /// number of preferred bands to use (meaningful only in PREFERRED mode)
    int numBands_;                      /// number of cell bands

    // Feedback Maps
    //typedef std::map<Remote,LteFeedback> FeedbackMap_;
    LteFeedbackDoubleVector periodicFeedback;
    LteFeedbackDoubleVector aperiodicFeedback;

    //MacNodeID
    MacNodeId masterId_;
    MacNodeId nodeId_;

    bool feedbackComputationPisa_;
    /**
     * NOTE: fbPeriod_ MUST be greater than fbDelay_,
     * otherwise we have overlapping transmissions
     * for periodic feedback (when calling start() on busy
     * transmission timer we have no operation)
     */
    simtime_t fbPeriod_;    /// period for Periodic feedback in TTI
    simtime_t fbDelay_;     /// time interval between sensing and transmission in TTI
private:

    /**
     * DUMMY: should be provided by PHY
     */
    void sendFeedback(LteFeedbackDoubleVector fb, FbPeriodicity per);


    LteFeedbackComputation* getFeedbackComputationFromName(std::string name, ParameterMap& params);


protected:

    /**
     * Initialization function.
     */
    virtual void initialize(int stage);

    /**
     * Manage self messages for sensing and transmission.
     * @param msg self message for sensing or transmission
     */
    virtual void handleMessage(cMessage *msg);

    /**
     * Channel sensing
     */
    void sensing(FbPeriodicity per);
    virtual int numInitStages() const { return inet::INITSTAGE_LINK_LAYER_2 + 1; }

public:

    /**
     * Constructor
     */
    LteDlFeedbackGenerator();

    /**
     * Destructor
     */
    ~LteDlFeedbackGenerator();

    /**
     * Function used to register an aperiodic feedback request
     * to the Downlink Feedback Generator.
     * Called by PHY.
     */
    void aperiodicRequest();

    /**
     * Function used to set the current Tx Mode.
     * Called by PHY.
     * @param newTxMode new transmission mode
     */
    void setTxMode(TxMode newTxMode);

    /*
     * Perform handover-related operations
     * Update cell id and the reference to the cellInfo
     */
    void handleHandover(MacCellId newEnbId);
};

#endif
