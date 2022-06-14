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

#ifndef __ARTERY_LTESIDELINKGRANT_H_
#define __ARTERY_LTESIDELINKGRANT_H_

#include <omnetpp.h>
#include "stack/mac/packet/LteSchedulingGrant.h"
using namespace omnetpp;

/**
 * TODO - Generated class
 */
class LteSidelinkGrant : public LteSchedulingGrant
{
protected:
    simtime_t startTime;

    bool retransmission;
    bool firstTransmission;
    unsigned int timeGapTransRetrans;
    unsigned int priority;
    unsigned int numSubchannels;
    double minGrantStartTime;
    double maximumLatency;
    unsigned int startingSubchannel;
    unsigned int mcs;
    unsigned int retransSubchannel; // It is possible the retransmission has different resources assigned to it.
    unsigned int resourceReselectionCounter;
    int totalGrantedBlocks;
    int rri;
    int transmitBlockSize;
    unsigned int expiryCounter;
    double expiryTime;
    int packetId;
    int CAMId;
    MacNodeId destId;
    double nextArrival;
    bool freshAllocation;
    bool activateGrant;
    int subsetRBActivate;
    std::vector<double> grantSubsequent;


public:

    LteSidelinkGrant(const char *name = NULL, int kind = 0) :
        LteSchedulingGrant(name, kind)
    {
        numSubchannels = 0;
        priority =0;
        rri = 0;
        minGrantStartTime = 0.0;
        maximumLatency = 0.0;
        timeGapTransRetrans = 0;
        startingSubchannel = 0;
        mcs = 0;
        expiryTime = 0.0;
        retransSubchannel = 0;
        totalGrantedBlocks = 0;
        resourceReselectionCounter = 0;
        expiryCounter = 0;
        freshAllocation = false;
        firstTransmission = true;
        activateGrant = true;
        subsetRBActivate = 0.0;
        startTime = simTime();
        packetId = 0;
        CAMId = 0;
        nextArrival = 0.0;
        grantSubsequent.clear();
    }


    ~LteSidelinkGrant()
    {
   /* if (userTxParams != NULL)
            {
                delete userTxParams;
                userTxParams = NULL;
            }*/
    }
    LteSidelinkGrant(const LteSidelinkGrant& other) :
        LteSchedulingGrant(other.getName())
    {
        operator=(other);
    }

    LteSidelinkGrant& operator=(const LteSidelinkGrant& other)
    {
        numSubchannels = other.numSubchannels;
        totalGrantedBlocks = other.totalGrantedBlocks;
        startTime = other.startTime;
        minGrantStartTime = other.minGrantStartTime ;
        maximumLatency = other.maximumLatency;
        priority = other.priority;
        freshAllocation = other.freshAllocation;
        expiryCounter = other.expiryCounter;
        timeGapTransRetrans = other.timeGapTransRetrans;
        startingSubchannel = other.startingSubchannel;
        mcs = other.mcs;
        retransSubchannel = other.retransSubchannel;
        resourceReselectionCounter = other.resourceReselectionCounter;
        rri = other.rri;
        destId = other.destId;
        activateGrant = other.activateGrant;
        subsetRBActivate = other.subsetRBActivate;
        expiryTime = other.expiryTime;
        packetId = other.packetId;
        CAMId  = other.CAMId;
        nextArrival = other.nextArrival;
        grantSubsequent = other.grantSubsequent;
        LteSchedulingGrant::operator=(other);
        return *this;
    }

    virtual LteSidelinkGrant *dup() const
    {
        return new LteSidelinkGrant(*this);
    }

    void setStartTime(simtime_t start)
    {
        startTime = start;
    }
    simtime_t getStartTime() const
    {
        return startTime;
    }

    void setNumberSubchannels(unsigned int subchannels)
    {
        numSubchannels = subchannels;
    }
    unsigned int getNumSubchannels() const
    {
        return numSubchannels;
    }
    void setMaximumLatency(unsigned int maxLatency)
    {
        maximumLatency = maxLatency;
    }
    unsigned int getMaximumLatency() const
    {
        return maximumLatency;
    }
    void setTimeGapTransRetrans(unsigned int timeGapTransRetrans)
    {
        this->timeGapTransRetrans = timeGapTransRetrans;
    }
    unsigned int getTimeGapTransRetrans() const
    {
        return timeGapTransRetrans;
    }
    void setStartingSubchannel(unsigned int subchannelIndex)
    {
        this->startingSubchannel = subchannelIndex;
    }
    unsigned int getStartingSubchannel() const
    {
        return startingSubchannel;
    }
    void setMcs(unsigned int mcs)
    {
        this->mcs = mcs;
    }
    unsigned int getMcs() const
    {
        return mcs;
    }

    void setTransmitBlockSize(int tbSize)
        {

            this->transmitBlockSize = tbSize;
        }
    int getTransmitBlockSize()
    {
        return transmitBlockSize;
    }

    void setRetransSubchannel(unsigned int retransSubchannel)
    {
        this->retransSubchannel = retransSubchannel;
    }
    unsigned int getRetransSubchannel() const
    {
        return retransSubchannel;
    }
    void setResourceReselectionCounter(unsigned int resourceReselectionCounter)
    {
        this->resourceReselectionCounter = resourceReselectionCounter;
    }
    unsigned int getResourceReselectionCounter() const
    {
        return resourceReselectionCounter;
    }
    void setRetransmission(bool retransmission)
    {
        this->retransmission = retransmission;
    }
    bool getRetransmission() const
    {
        return retransmission;
    }

    bool getFirstTransmission() const
    {
        return firstTransmission;
    }
    void setFirstTransmission(bool firstTransmission)
    {
        this->firstTransmission = firstTransmission;
    }

    MacNodeId getDestId() const {
        return destId;
    }

    void setDestId(MacNodeId destId) {
        this->destId = destId;
    }


    void setPacketId(int pid)
    {
        this->packetId = pid;
    }
    int getPacketId()
    {
        return packetId;
    }

    int getCamId()  {
        return CAMId;
    }

    void setCamId(int camId) {
        CAMId = camId;
    }

    double getNextArrival(){
        return nextArrival;
    }

    void setNextArrival(double nextArrival) {
        this->nextArrival = nextArrival;
    }

    double getMinGrantStartTime()  {
        return minGrantStartTime;
    }

    void setMinGrantStartTime(double minGrantStartTime) {
        this->minGrantStartTime = minGrantStartTime;
    }

    unsigned int getPriority(){
        return priority;
    }

    void setPriority(unsigned int priority) {
        this->priority = priority;
    }

    int getRri()  {
        return rri;
    }

    void setRri(int rri) {
        this->rri = rri;
    }

    int getTotalGrantedBlocks()  {
        return totalGrantedBlocks;
    }

    void setTotalGrantedBlocks(int totalGrantedBlocks) {
        this->totalGrantedBlocks = totalGrantedBlocks;
    }

    double getExpiryTime()  {
        return expiryTime;
    }

    void setExpiryTime(double expiryTime) {
        this->expiryTime = expiryTime;
    }

    unsigned int getExpiryCounter()  {
        return expiryCounter;
    }

    void setExpiryCounter(unsigned int expiryCounter) {
        this->expiryCounter = expiryCounter;
    }

    bool isFreshAllocation() {
        return freshAllocation;
    }

    void setFreshAllocation(bool freshAllocation) {
        this->freshAllocation = freshAllocation;
    }

    bool isActivateGrant() const {
        return activateGrant;
    }

    void setActivateGrant(bool activateGrant) {
        this->activateGrant = activateGrant;
    }

    int getSubsetRbActivate() const {
        return subsetRBActivate;
    }

    void setSubsetRbActivate(int subsetRbActivate) {
        subsetRBActivate = subsetRbActivate;
    }

     std::vector<double>& getGrantSubsequent()  {
        return grantSubsequent;
    }

    void setGrantSubsequent( std::vector<double> &grantSubsequent) {
        this->grantSubsequent = grantSubsequent;
    }
};





#endif
