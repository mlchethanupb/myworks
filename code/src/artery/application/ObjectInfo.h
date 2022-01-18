//
// Created by rosk on 13.02.19.
//

#ifndef ARTERY_OBJECTINFO_H
#define ARTERY_OBJECTINFO_H

#include "artery/application/ItsG5BaseService.h"
#include "artery/utility/Geometry.h"
#include <vanetza/asn1/cpm.hpp>
#include <artery/envmod/LocalEnvironmentModel.h>
#include <artery/envmod/EnvironmentModelObject.h>
#include <vanetza/btp/data_interface.hpp>
#include <vanetza/units/angle.hpp>
#include <vanetza/units/velocity.hpp>
#include <omnetpp/simtime.h>
#include "artery/application/Configurations.h"


namespace artery
{

class ObjectInfo
{
public:
    using ObjectsPercievedMap = std::map<const LocalEnvironmentModel::Object, ObjectInfo, std::owner_less<LocalEnvironmentModel::Object>>;
    using ObjectPercieved = typename ObjectsPercievedMap::value_type;
    using ObjectsReceivedMap = std::map<const uint32_t, ObjectInfo>;

    ObjectInfo();
    ObjectInfo(bool, LocalEnvironmentModel::TrackingTime, Identifier_t&,
                    vanetza::units::Angle, bool, Position, vanetza::units::Velocity);

    bool getHasV2XCapabilities() const { return mHasV2XCapabilities;}
    LocalEnvironmentModel::TrackingTime& getLastTrackingTime() { return mLastTrackingTime; }
    size_t getNumberOfSensors() const { return mNumberOfSensors; }
    Identifier_t getSensorId() const { return mSensorsId; }
    vanetza::units::Angle getLastHeading(){return mLastCpmHeading;}
    Position getLastPosition(){return mLastCpmPosition;}
    vanetza::units::Velocity getLastVelocity(){return mLastCpmSpeed;}
    bool getHeadingAvailable(){return mHeadingAvailable;}
    void setLastTrackingTime(LocalEnvironmentModel::TrackingTime lastTrackingTime) {mLastTrackingTime = lastTrackingTime;}
    void setNumberOfSensors(size_t numberOfSensors) {mNumberOfSensors = numberOfSensors;}
    void setSensorId(Identifier_t& id) {mSensorsId = id;}
    void setHasV2XCapabilities(bool hasV2XCapabilities) {mHasV2XCapabilities = hasV2XCapabilities;}
    static void printObjectsReceivedMap(ObjectsReceivedMap objReceived);
    static void printObjectsToSendMap(ObjectsPercievedMap objMap);
    void setLastTimeSent(omnetpp::SimTime time) { mLastTimeSent = time;}
    omnetpp::SimTime getLastTimeSent() { return mLastTimeSent; }


private:
    LocalEnvironmentModel::TrackingTime mLastTrackingTime;
    size_t mNumberOfSensors;
    Identifier_t mSensorsId;
    vanetza::units::Angle mLastCpmHeading;
    Position mLastCpmPosition;
    vanetza::units::Velocity mLastCpmSpeed;
    bool mHasV2XCapabilities = false;
    bool mHeadingAvailable = false;
    omnetpp::SimTime mLastTimeSent;
};

std::ostream& operator<<(std::ostream& os, ObjectInfo& infoObj);

} //end namespace artery

#endif //ARTERY_OBJECTINFO_H
