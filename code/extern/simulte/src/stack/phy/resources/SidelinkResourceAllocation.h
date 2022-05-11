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

#ifndef __ARTERY_SIDELINKRESOURCEALLOCATION_H_
#define __ARTERY_SIDELINKRESOURCEALLOCATION_H_

#include <omnetpp.h>
#include <map>
#include <vector>
#include "boost/tuple/tuple.hpp"
#include <bits/stdc++.h>
#include <algorithm>
#include <iostream>
#include <utility>      //
#include <algorithm>
#include "stack/phy/packet/SidelinkControlInformation_m.h"
#include "stack/mac/packet/LteSchedulingGrant.h"
#include "stack/mac/allocator/LteAllocationModule.h"
#include <unordered_map>
#include "stack/phy/packet/LteAirFrame.h"
#include "common/LteControlInfo_m.h"
#include "stack/phy/resources/Subchannel.h"
#include "corenetwork/lteCellInfo/LteCellInfo.h"
#include "common/LteCommon.h"
#include "stack/mac/packet/LteSidelinkGrant.h"
#include "stack/phy/layer/LtePhyUe.h"
#include "stack/phy/layer/LtePhyBase.h"
#include "corenetwork/binder/LteBinder.h"
#include "stack/phy/ChannelModel/LteRealisticChannelModel.h"
#include "stack/mac/amc/LteAmc.h"
#include "stack/phy/packet/cbr_m.h"
#include<bitset>
#include <stdlib.h>
#include "stack/phy/ChannelModel/LteRealisticChannelModel.h"
#include  "stack/phy/packet/SidelinkSynchronization_m.h"
#include "stack/phy/resources/Subchannel.h"
#include <boost/circular_buffer.hpp>
#include <numeric>
#include <assert.h>
#include <bits/stdc++.h>
using namespace omnetpp;
using namespace std;

/**
 * TODO - Generated class
 */
class SidelinkResourceAllocation : public cSimpleModule
{
public:
    struct UsedRBs
    {
        simtime_t time_;
        RbMap rbMap_;


    };

    LteSidelinkGrant* sciGrant_;
    LteRealisticChannelModel* channelModel_;
    Subchannel* subch;
    LteNodeType nodeType_;
    RbMap availableRBs_;
    SidelinkResourceAllocation* allocator_;
    LteCellInfo* deployer_;
    LteBinder* binder_;

    double d2dTxPower_;
    unsigned int numAirFrameReceived_;
    unsigned int numAirFrameNotReceived_;
    bool adjacencyPSCCHPSSCH_; //
    int pStep_; //
    int numSubchannels_; //
    int subchannelSize_ ;//
    int selectionWindowStartingSubframe_;
    int thresholdRSSI_;
    bool transmitting_;
    int numberSubcarriersperPRB;
    int numberSymbolsPerSlot;
    int bitsPerSymbolQPSK;
    int numberPRBTransmitBlock;
    int subChRBStart_;
    int numberPRBSCI;
    int sciFlag;
    int tbFlag;
    int sciReceived_;
    int sciDecoded_;
    int sciNotDecoded_;
    int tbReceived_;
    int tbDecoded_;
    int tbFailedDueToNoSCI_;
    int tbFailedButSCIReceived_;
    int tbAndSCINotReceived_;
    int sciFailedHalfDuplex_;
    int tbFailedHalfDuplex_;
    int subchannelReceived_;
    int subchannelsUsed_;
    int pRsvpTx;
    int cResel;
    double maxLatency;
    int totalPossibleCSRs;
    int lengthBitMap;
    int countHD;
    double txPower_;
    double tSync;
    int allocatedBlocksPrevious;
    double FirstTransmission;
    int pcCountMode4;
    bool packetDrop;

    //Sensing window parameters

    simtime_t subframeTime ;
    double rssiReception;
    double rsrpReception;
    bool txStatus;
    bool rxStatus;
    //Congestion control parameters
    double cbr;
    double cr;
    double rsrpThreshold_;
    double rssiThreshold_;
    double crLimit;
    bool crLimitReached;
    int occupiedResourceBlocks;
    double averageCbr;


    std::vector<int> allocatedPRBSciIndex;
    std::vector<int> allocatedPRBTBIndex;
    std::vector<int> ThresPSSCHRSRPvector_;
    std::vector<int> subframeBitMap;
    std::vector<LteAirFrame*> tbFrames_; // airframes received in the current TTI. Only one will be decoded
    std::vector<std::vector<double>> tbRsrpVectors_;
    std::vector<std::vector<double>> tbRssiVectors_;
    std::vector<std::vector<Subchannel*>> sensingWindow_;
    std::vector<Subchannel*> subframe;
    int sensingWindowFront_;
    std::vector<std::vector<double>> sciRsrpVectors_;
    std::vector<std::vector<double>> sciRssiVectors_;
    std::vector<LteAirFrame*> sciFrames_;
    std::vector<cPacket*> scis_;
    std::vector<double> candidateSubframes;
    std::vector<int> RBIndicesSCI ;
    std::vector<int> RBIndicesData;
    std::vector<int> RBIndicesDataPrevious;
    std::string rrcCurrentState;
    std::vector<UsedRBs> usedRbs_;
    std::vector<double> allowedRRIs;
    std::vector<std::tuple<double, int, double>> optimalCSRs;
    std::vector<std::tuple<double,std::vector<int>,std::vector<int>>> resourceAllocationMap;
    typedef std::tuple<double, double,double,bool,bool>  sensingVector;
    typedef std::tuple<double, double>  cbrParamsVector;
    typedef std::tuple<double, int>  freqAllocationParams;
    sensingVector s1;
    cbrParamsVector c1;
    freqAllocationParams f1;
    boost::circular_buffer<sensingVector> sensingWindow ;
    boost::circular_buffer<cbrParamsVector> cbrWindow;
    boost::circular_buffer<freqAllocationParams> freqAllocationMap;

    MacNodeId nodeId_;
    MacNodeId masterId_;
    MacNodeId  connectedNodeId_;

    /** Self message to start the handover procedure */
    cMessage *handoverTrigger_;
    cMessage *handoverStarter_;
    cMessage* d2dDecodingTimer_; // timer for triggering decoding at the end of the TTI. Started when the first airframe is received
    cMessage* slsync;
    simtime_t nextSLSS;
    simtime_t lastActive_;
    simsignal_t numberSubchannels;
    simsignal_t totalCSR;
    simsignal_t syncLatency;
    simsignal_t resourceAllocationLatency;
    simsignal_t configurationLatency;
    simsignal_t halfDuplexError;
    simsignal_t pcMode4;

    simtime_t getLastActive() { return lastActive_; }
    simtime_t sidelinkSynchronization(bool);

    void storeAirFrame(LteAirFrame* frame, UserControlInfo* lteInfo);
    LteAirFrame* extractAirFrame();
    void decodeAirFrame(LteAirFrame* frame, UserControlInfo* lteInfo);
    // ---------------------------------------------------------------- //

    virtual void initialize(int stage);
    virtual void handleMessage(cMessage* msg);
    virtual void finish();

    virtual void handleUpperMessage(cMessage* msg);
    virtual void handleSelfMessage(cMessage *msg);
    // Helper function which prepares a frame for sending
    // Generate an SCI message corresponding to a Grant
    virtual LteAirFrame* createSCIMessage(cMessage* msg,  LteSidelinkGrant* grant);
    // Compute Candidate Single Subframe Resources which the MAC layer can use for transmission
    virtual   std::vector<int> getallocationSciIndex(int subChRBStart_);
    virtual std::tuple<int,int> decodeRivValue(SidelinkControlInformation* sci, UserControlInfo* sciInfo);
    virtual LteAirFrame* prepareAirFrame(cMessage* msg, UserControlInfo* lteInfo);
    virtual void  initialiseSensingWindow();
    boost::circular_buffer<sensingVector> updateSensingWindow(double, double, double, bool, bool);
    virtual void computeCSRs(LteSidelinkGrant* , LteNodeType );
    std::vector<std::tuple<double, int, double>> selectBestRSSIs(std::vector<double> subframes, LteSidelinkGrant* &grant, double subFrame );

    //Congestion control parameters
    double calculateChannelBusyRatio(int);
    bool checkCRLimit(double cbr,double cr);
    boost::circular_buffer<std::tuple<double, double>>  updateCbrWindow(double subframeTime,double cbr);
    void  initialiseCbrWindow();
    void initialiseFreqAllocationMap();
    boost::circular_buffer<std::tuple<double, int>>  updateFreqAllocationMap(double subframeTime, int allocatedRB);
    double calculateChannelOccupancyRatio(boost::circular_buffer<std::tuple<double, int>> ,int );
public:
    SidelinkResourceAllocation();
    virtual ~SidelinkResourceAllocation();
    std::vector<int> getallocationTBIndex(int bitLength,   std::vector<int>);
    int getReselectionCounter() const
    {
        return cResel;
    }

    void setReselectionCounter(int resel)
    {
        cResel = resel;
    }

    virtual double getTxPwr(Direction dir = UNKNOWN_DIRECTION)
    {
        if (dir == D2D)
            return d2dTxPower_;
        return 22.00;
    }

    int getAllocatedBlocksPrevious() const
    {
        return allocatedBlocksPrevious;
    }

    void setAllocatedBlocksPrevious(int allocatedBlocksPrevious)
    {
        this->allocatedBlocksPrevious = allocatedBlocksPrevious;
    }
    void setPreviousSubchannelsData(std::vector<int> subchannels)
    {
        RBIndicesDataPrevious = subchannels;
    }
    std::vector<int> getPreviousSubchannelsData()
                                                {
        return RBIndicesDataPrevious;
                                                }
    std::vector<int>& getAllocatedPrbSciIndex()  {
        return allocatedPRBSciIndex;
    }

    void setAllocatedPrbSciIndex(
            std::vector<int> &allocatedPrbSciIndex) {
        allocatedPRBSciIndex = allocatedPrbSciIndex;
    }

    std::vector<int>& getAllocatedPrbtbIndex()  {
        return allocatedPRBTBIndex;
    }

    void setAllocatedPrbtbIndex(
            std::vector<int> &allocatedPrbtbIndex) {
        allocatedPRBTBIndex = allocatedPrbtbIndex;
    }

    void setFirstTransmissionPrevious(double firstTransmission)
    {
        FirstTransmission = firstTransmission;
    }
    double getFirstTransmissionPrevious()
    {
        return FirstTransmission;
    }
    const boost::circular_buffer<sensingVector>& getSensingWindow() const {
        return sensingWindow;
    }

    void setSensingWindow(
            const boost::circular_buffer<sensingVector> &sensingWindow) {
        this->sensingWindow = sensingWindow;
    }
    boost::circular_buffer<cbrParamsVector>& getCbrWindow(){
        return cbrWindow;
    }

    void setCbrWindow(
            boost::circular_buffer<cbrParamsVector> &cbrWindow) {
        this->cbrWindow = cbrWindow;
    }

    int getOccupiedResourceBlocks() {
        return occupiedResourceBlocks;
    }

    void setOccupiedResourceBlocks(int occupiedResourceBlocks) {
        this->occupiedResourceBlocks = occupiedResourceBlocks;
    }
    boost::circular_buffer<freqAllocationParams>& getFreqAllocationMap()  {
        return freqAllocationMap;
    }

    void setFreqAllocationMap(
            boost::circular_buffer<freqAllocationParams> &freqAllocationMap) {
        this->freqAllocationMap = freqAllocationMap;
    }
};

#endif
