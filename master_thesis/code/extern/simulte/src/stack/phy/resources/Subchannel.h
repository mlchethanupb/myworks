
#ifndef _ARTERY_SUBCHANNEL_H_
#define _ARTERY_SUBCHANNEL_H_


#include <omnetpp.h>
#include "common/LteCommon.h"
#include "stack/phy/packet/SidelinkControlInformation_m.h"


class Subchannel
{
protected:
    int numRbs;
    bool reserved;
    bool sensed;
    bool possibleCSR;
    int priority;
    int resourceReservationInterval;
    int frequencyResourceLocation;
    int timeGapRetrans;
    int mcs;
    int retransmissionIndex;
    int sciSubchannelIndex;
    int sciLength;
    int sum;
    std::vector<Band> occupiedBands;
    std::map<Band, double> rsrpValues;
    std::map<Band, double> rssiValues;
    std::vector<std::pair<Band,double>> rssiVector;
    simtime_t subframeTime;
public:
    Subchannel(const int subchannelSize, simtime_t simulationTime)
{
        numRbs = subchannelSize;
        reserved = false;
        sensed = true;
        possibleCSR = true;
        subframeTime = simulationTime;
        sciLength = 0;
        sciSubchannelIndex = 0;
}


    ~Subchannel()
    {
    }

    Subchannel(const Subchannel& other)
    {
        operator=(other);
    }

    Subchannel& operator=(const Subchannel& other)
    {
        numRbs = other.numRbs;
        reserved = other.reserved;
        subframeTime = other.subframeTime;
        priority = other.priority;
        resourceReservationInterval = other.resourceReservationInterval;
        frequencyResourceLocation = other.frequencyResourceLocation;
        timeGapRetrans = other.timeGapRetrans;
        mcs = other.mcs;
        retransmissionIndex = other.retransmissionIndex;
        sciSubchannelIndex = other.sciSubchannelIndex;
        sciLength = other.sciLength;
        rsrpValues = other.rsrpValues;
        rssiValues = other.rssiValues;
        occupiedBands = other.occupiedBands;
        sensed = other.sensed;
        possibleCSR = other.possibleCSR;
        return *this;
    }

    virtual Subchannel *dup() const
    {
        return new Subchannel(*this);
    }

    void setSubframeTime(simtime_t subframeTime)
    {
        this->subframeTime = subframeTime;
    }
    simtime_t getSubframeTime() const
    {
        return subframeTime;
    }
    void setNumRbs(int numRbs)
    {
        this->numRbs = numRbs;
    }
    int getNumRbs() const
    {
        return numRbs;
    }
    void setReserved(bool reserved)
    {
        this->reserved = reserved;
    }
    bool getReserved() const
    {
        return reserved;
    }
    double getAverageRSRP()
    {
        if (rsrpValues.size() != 0) {
            double sum = 0;
            std::map<Band, double>::iterator it;
            for (it = rsrpValues.begin(); it != rsrpValues.end(); it++) {
                sum += it->second;
            }
            return sum / numRbs;
        } else {
            return -std::numeric_limits<double>::infinity();
        }
    }
    double getAverageRSSI(std::vector<std::pair<Band,double>> rssiVector)
    {

        EV<<"Computing average RSSI over bands"<<endl;
        sum = 0;
        std::vector<std::pair<Band,double>>::iterator it = rssiVector.begin();
        numRbs = 6;

        for(; it!=rssiVector.end(); it++)
        {
            sum += it->second;
            EV<<"sum: "<<sum<<" "<<"Band: "<<it->first<<endl;
        }
        return sum/numRbs;

        if (rssiVector.size()==0)
        {
            return - std::numeric_limits<double>::infinity();
        }

        rssiVector.clear();
    }

    void addRsrpValue(double rsrpValue, Band band)
    {
        auto it = rsrpValues.find(band);
        if (it != rsrpValues.end()) {
            if (it->second > rsrpValue){
                it->second = rsrpValue;
            }
        } else {
            rsrpValues[band] = rsrpValue;
        }
    }
    void addRssiValue(double rssiValue, Band band)
    {
        auto it = rssiValues.find(band);
        if (it != rssiValues.end()) {
            if (it->second > rssiValue){
                it->second = rssiValue;
            }
        } else {
            rssiValues[band] = rssiValue;
        }

    }
    std::vector<Band> getOccupiedBands() const
                {
        return occupiedBands;
                }
    void setOccupiedBands(std::vector<Band> occupiedBands)
    {
        this->occupiedBands = occupiedBands;
    }
    void setSensed(bool sensed)
    {
        this->sensed = sensed;
    }
    bool getSensed() const
    {
        return sensed;
    }
    void setPossibleCSR(bool possibleCSR)
    {
        this->possibleCSR = possibleCSR;
    }
    bool getPossibleCSR() const
    {
        return possibleCSR;
    }
    void setPriority(int priority)
    {
        this->priority = priority;
    }
    int getPriority()
    {
        return priority;
    }
    void setResourceReservationInterval(int resourceReservationInterval)
    {
        this->resourceReservationInterval = resourceReservationInterval;
    }
    int getResourceReservationInterval()
    {
        return resourceReservationInterval;
    }
    void setFrequencyResourceLocation(int frequencyResourceLocation)
    {
        this->frequencyResourceLocation = frequencyResourceLocation;
    }
    int getFrequencyResourceLocation()
    {
        return frequencyResourceLocation;
    }
    void setMcs (int mcs)
    {
        this->mcs = mcs;
    }
    int getMcs()
    {
        return mcs;
    }
    void setRetransmissionIndex(int retransmissionIndex)
    {
        this->retransmissionIndex = retransmissionIndex;
    }
    int getRetransmissionIndex()
    {
        return retransmissionIndex;
    }
    void setTimeGapRetrans(int timeGapRetrans)
    {
        this->timeGapRetrans = timeGapRetrans;
    }
    int getTimeGapRetrans()
    {
        return timeGapRetrans;
    }
    void setSciSubchannelIndex(int sciSubchannelIndex)
    {
        this->sciSubchannelIndex = sciSubchannelIndex;
    }
    int getSciSubchannelIndex()
    {
        return sciSubchannelIndex;
    }
    void setSciLength(int sciLength)
    {
        this->sciLength = sciLength;
    }
    int getSciLength()
    {
        return sciLength;
    }
    void reset(simtime_t simulationTime)
    {
        reserved = false;
        sensed = true;
        possibleCSR = true;
        subframeTime = simulationTime;
        rsrpValues.clear();
        rssiValues.clear();
        priority = 0;
        resourceReservationInterval = 0;
        frequencyResourceLocation = 0;
        timeGapRetrans = 0;
        mcs = 0;
        retransmissionIndex = 0;
        sciSubchannelIndex = 0;
        sciLength = 0;
    }
};

#endif /* RADIODRIVERPROPERTIES_H_4GALJBTN */

