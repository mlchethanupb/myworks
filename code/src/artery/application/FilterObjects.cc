//
// Created by rosk on 03.02.19.
//
#include "FilterObjects.h"

#include "artery/application/CpObject.h"
#include "artery/application/Asn1PacketVisitor.h"
#include "artery/application/VehicleDataProvider.h"
#include "artery/utility/simtime_cast.h"
#include "veins/base/utils/Coord.h"

#include "artery/application/Configurations.h"
#include "artery/envmod/sensor/Sensor.h"

#include <boost/units/cmath.hpp>
#include <boost/units/systems/si/prefixes.hpp>
#include <omnetpp/cexception.h>
#include <vanetza/btp/ports.hpp>
#include <vanetza/dcc/transmission.hpp>
#include <vanetza/facilities/cam_functions.hpp>
#include <vanetza/dcc/transmit_rate_control.hpp>
#include <chrono>
#include <iostream>

/** Template to do a filter:
 * Create a function that return False if the object should not be sent
 * True otherwise
 * Add filter in the filterObjects function
 *
 * In CPService initialize(), add an entry for the filter added
 */

namespace artery
{


FilterObjects::FilterObjects(){}

FilterObjects::FilterObjects(const VehicleDataProvider* vd, LocalEnvironmentModel* le, std::vector<bool> filtersEnabled,
                             vanetza::units::Angle hd, vanetza::units::Length pd, vanetza::units::Velocity sd,
                             std::map<const Sensor*, Identifier_t>* sensorsId, const omnetpp::SimTime& T_GenCpmMin,
                            const SimTime& T_GenCpmMax):
        mVehicleDataProvider(vd), mLocalEnvironmentModel(le), mFiltersEnabled(filtersEnabled),
        mHeadingDelta(hd), mPositionDelta(pd), mSpeedDelta(sd), mSensorsId(sensorsId), mGenCpmMin(T_GenCpmMin),
        mGenCpmMax(T_GenCpmMax)
{
}


template<typename T, typename U>
long round(const boost::units::quantity<T>& q, const U& u)
{
    boost::units::quantity<U> v { q };
    return std::round(v.value());
}


void FilterObjects::initialize(const VehicleDataProvider* vd, LocalEnvironmentModel* le, std::vector<bool> filtersEnabled,
                                 vanetza::units::Angle hd, vanetza::units::Length pd, vanetza::units::Velocity sd,
                                 std::map<const Sensor*, Identifier_t>* sensorsId, const omnetpp::SimTime& T_GenCpmMin,
                                 const omnetpp::SimTime& T_GenCpmMax)
{
    mVehicleDataProvider = vd;
    mLocalEnvironmentModel= le;
    mFiltersEnabled = filtersEnabled;
    mHeadingDelta = hd;
    mPositionDelta = pd;
    mSpeedDelta = sd;
    mSensorsId = sensorsId;
    mGenCpmMin = T_GenCpmMin;
    mGenCpmMax = T_GenCpmMax;
    mTimeDelta = omnetpp::SimTime(1, SIMTIME_S);
}


bool FilterObjects::checkHeadingDelta(vanetza::units::Angle prevHeading, vanetza::units::Angle headingNow) const
{
 //   std::cout << "Heading: " << std::endl;
 //   std::cout << round(prevHeading, vanetza::units::degree) << "  " << round(headingNow, vanetza::units::degree) << std::endl;

    return !vanetza::facilities::similar_heading(prevHeading, headingNow, mHeadingDelta);
}


bool FilterObjects::checkPositionDelta(Position prevPos, Position posNow) const
{
    /*std::cout << "Position: " << std::endl;
    std::cout <<  prevPos.x /  boost::units::si::meter
              << ", " << prevPos.y /  boost::units::si::meter << std::endl;
    std::cout <<  posNow.x /  boost::units::si::meter
              << ", " << posNow.y /  boost::units::si::meter << std::endl;
    std::cout << distance(prevPos, posNow) / boost::units::si::meter << std::endl;
    */
    return (distance(prevPos, posNow) > mPositionDelta);
}


bool FilterObjects::checkSpeedDelta(vanetza::units::Velocity prevVel,  vanetza::units::Velocity velNow) const
{
    /*
    std::cout << "Speed: " << std::endl;

    std::cout << prevVel / vanetza::units::si::meter_per_second << std::endl;
    std::cout << velNow / vanetza::units::si::meter_per_second << std::endl;
    std::cout << abs(prevVel - velNow) / vanetza::units::si::meter_per_second << std::endl;
    */
    return abs(prevVel - velNow) > mSpeedDelta;
}


bool FilterObjects::checkTimeDelta(omnetpp::SimTime T_prev, omnetpp::SimTime T_now) const
{
    /*std::cout << "New check time " << std::endl;
    std::cout << T_prev << std::endl;
    std::cout << mTimeDelta << std::endl;
    std::cout << T_now << std::endl;
    std::cout << T_prev + mTimeDelta << std::endl;
    */
    return T_prev + mTimeDelta < T_now;
}


void FilterObjects::changeDeltas(vanetza::units::Angle hd, vanetza::units::Length pd, vanetza::units::Velocity sd){
    mHeadingDelta = hd;
    mPositionDelta = pd;
    mSpeedDelta = sd;
}


std::size_t FilterObjects::filterObjects(ObjectInfo::ObjectsTrackedMap &objToSend,
                                  ObjectInfo::ObjectsTrackedMap &prevObjSent, omnetpp::SimTime T_GenCpmDcc,
                                  Sensor * cpSensor, ObjectInfo::ObjectsReceivedMap& objReceived, const SimTime& T_now){
    std::size_t countObject = 0;
    //Go through all the objects tracked
    for(const LocalEnvironmentModel::TrackedObject& obj : mLocalEnvironmentModel->allObjects()){

        const artery::LocalEnvironmentModel::Tracking& tracking_ptr = obj.second;
        const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection =  tracking_ptr.sensors();

        bool detectedByRadars = false;
        for(const auto& tracker : sensorsDetection) {
            if (tracker.first->getSensorCategory() == "Radar") {
                detectedByRadars = true;
                break;
            }
        }

        //Remove all expired object
        const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();
        if (objReceived.find(vd.station_id()) != objReceived.end()) {
            ObjectInfo &infoObjectAI = objReceived.at(vd.station_id());
            //Remove the entry if expired
            if (objReceived.at(vd.station_id()).getLastTrackingTime().last() +
                cpSensor->getValidityPeriod() < mVehicleDataProvider->updated()) {
                objReceived.erase(vd.station_id());
            }
        }

        //Remove objects not detected by the local sensors (Radars, cameras, Lidar)
        if(!detectedByRadars)
            continue;

        countObject++;

        if(mFiltersEnabled[0] && !v2xCapabilities(obj, sensorsDetection, objReceived))
            continue;

        if(mFiltersEnabled[1] && !objectDynamicsLocal(obj, sensorsDetection, prevObjSent, T_now))
            continue;

        if(mFiltersEnabled[2] && !objectDynamicsV2X(obj, sensorsDetection, cpSensor, T_GenCpmDcc, objReceived))
            continue;

        if(mFiltersEnabled[3] && !fovSensors(obj, sensorsDetection, T_GenCpmDcc))
            continue;

        if(mFiltersEnabled[4] && !perceptionQuality(obj, sensorsDetection, T_GenCpmDcc))
            continue;

        if(mFiltersEnabled[5] && !updatingTime(obj, sensorsDetection, cpSensor, T_GenCpmDcc, objReceived, T_now))
            continue;

        if(mFiltersEnabled[6] && !etsiFilter(obj, sensorsDetection, prevObjSent, objReceived, T_now))
            continue;

        //If the object has been detected by its local perception capabilities (i.e. radar), add obj. to the list to send
        for(const auto& tracker : sensorsDetection){
            if(tracker.first->getSensorCategory() == "Radar"){

                //If object not already in the lists or if the current sensor has "more" updated information
                if(objToSend.find(obj.first) == objToSend.end() || objToSend.at(obj.first).getLastTrackingTime().last() < tracker.second.last()){
                    const auto& vd = obj.first.lock()->getVehicleData();
                    objToSend[obj.first] = ObjectInfo(false, tracker.second, mSensorsId->at(tracker.first), vd.heading(), true, vd.position(),  vd.speed());
                } //Both sensors checked the object at the same time
                else if (objToSend.at(obj.first).getLastTrackingTime().last() == tracker.second.last()){
                    objToSend.at(obj.first).setNumberOfSensors(objToSend.at(obj.first).getNumberOfSensors() + 1);
                }
            }
        }
    }
    return countObject;
}


void FilterObjects::getObjToSendNoFilter(ObjectInfo::ObjectsTrackedMap &objToSend, bool removeLowDynamics,
        ObjectInfo::ObjectsTrackedMap objectsPrevSent, const omnetpp::SimTime& T_now)
{
    //Go through all the objects tracked
    for(const LocalEnvironmentModel::TrackedObject& obj : mLocalEnvironmentModel->allObjects()){

        const artery::LocalEnvironmentModel::Tracking& tracking_ptr = obj.second;
        const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection =  tracking_ptr.sensors();

        bool detectedByRadars = false;
        for(const auto& tracker : sensorsDetection) {
            if (tracker.first->getSensorCategory() == "Radar") {
                detectedByRadars = true;
                break;
            }
        }

        //Remove objects not detected by the local sensors (Radars, cameras, Lidar)
        if(!detectedByRadars)
            continue;

        if(removeLowDynamics && !objectDynamicsLocal(obj, sensorsDetection, objectsPrevSent, T_now))
            continue;

        //If the object has been detected by its local perception capabilities (i.e. radar), add obj. to the list to send
        for(const auto& tracker : sensorsDetection){
            if(tracker.first->getSensorCategory() == "Radar"){

                //If object not already in the lists or if the current sensor has "more" updated information
                if(objToSend.find(obj.first) == objToSend.end() || objToSend.at(obj.first).getLastTrackingTime().last() < tracker.second.last()){
                    const auto& vd = obj.first.lock()->getVehicleData();
                    objToSend[obj.first] = ObjectInfo(false, tracker.second, mSensorsId->at(tracker.first), vd.heading(), true, vd.position(),  vd.speed());
                } //Both sensors checked the object at the same time
                else if (objToSend.at(obj.first).getLastTrackingTime().last() == tracker.second.last()){
                    objToSend.at(obj.first).setNumberOfSensors(objToSend.at(obj.first).getNumberOfSensors() + 1);
                }
            }
        }
    }
}


bool FilterObjects::v2xCapabilities(const LocalEnvironmentModel::TrackedObject& obj,
                                   const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                                   ObjectInfo::ObjectsReceivedMap& objReceived){

    const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();
    bool v2xEnabled = false;

    //Check that the object is detected by one of the local sensor and has already been perceived by someone
    if (objReceived.find(vd.station_id()) != objReceived.end()) {
        if (objReceived.at(vd.station_id()).getHasV2XCapabilities()){
            //std::cout << "Filter object "<< vd.station_id() << " because of V2X capabilities" << std::endl;
            return false;
        }
    }

    return true;
}


bool FilterObjects::objectDynamicsLocal(const LocalEnvironmentModel::TrackedObject& obj,
                                   const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                                   ObjectInfo::ObjectsTrackedMap& prevObjSent, omnetpp::SimTime T_now){

    //If the position of the object since last time it has been sent, refuse it
    if(prevObjSent.find(obj.first) != prevObjSent.end()) {

        const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();
        ObjectInfo &infoObject = prevObjSent.at(obj.first);

        //Object need to be send at least every one second
        if(T_now - infoObject.getLastTimeSent() >= omnetpp::SimTime(1, SIMTIME_S))
            return true;


        if (!(checkHeadingDelta(infoObject.getLastHeading(), vd.heading()) ||
              checkPositionDelta(infoObject.getLastPosition(), vd.position()) ||
              checkSpeedDelta(infoObject.getLastVelocity(), vd.speed()))){
            //std::cout << "\nObject dynamic local: Filter object "<< vd.station_id() << std::endl;
            return false;
        }
    }
    return true;
}


bool FilterObjects::objectDynamicsV2X(const LocalEnvironmentModel::TrackedObject& obj,
                                      const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                                      Sensor * cpSensor, omnetpp::SimTime T_GenCpmDcc,
                                      ObjectInfo::ObjectsReceivedMap& objReceived){

    const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();

    //Check that the object is detected by one of the local sensor and has already been perceived by someone
    if (objReceived.find(vd.station_id()) != objReceived.end()) {

        ObjectInfo &infoObjectAI = objReceived.at(vd.station_id());

        //Remove the entry if expired
        if (infoObjectAI.getLastTrackingTime().last() +
            cpSensor->getValidityPeriod() < mVehicleDataProvider->updated()) {
            objReceived.erase(vd.station_id());
            return true;
        }

        if(infoObjectAI.getHeadingAvailable()){
            if (!(checkPositionDelta(infoObjectAI.getLastPosition(), vd.position()) ||
                  checkSpeedDelta(infoObjectAI.getLastVelocity(), vd.speed()) ||
                  checkHeadingDelta(infoObjectAI.getLastHeading(), vd.heading()))) {
              // std::cout << "Refuse object for V2X kinematic change (check heading)" << std::endl;
               return false;
            }
        } else if (!(checkSpeedDelta(infoObjectAI.getLastVelocity(), vd.speed()) ||
                    checkPositionDelta(infoObjectAI.getLastPosition(), vd.position()))) {
            //std::cout << "Refuse object for V2X kinematic change (no heading check)" << std::endl;
            return false;
        }
    }

    return true;
}


bool FilterObjects::fovSensors(const LocalEnvironmentModel::TrackedObject& obj,
                                    const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                                    omnetpp::SimTime T_GenCpmDcc){

    const auto& vd = obj.first.lock()->getVehicleData();
    double ratio = (mGenCpmMax - T_GenCpmDcc) / (mGenCpmMax - mGenCpmMin);
    double coefCorrect = 1;

    //Filter on distance
    for(const auto& tracker : sensorsDetection) {

        if (tracker.first->getSensorCategory() == "Radar") {
            double distThresh = tracker.first->getFieldOfView()->range.value() * ratio * coefCorrect;
            if(distance(mVehicleDataProvider->position(), vd.position()) / boost::units::si::meter <= distThresh){
                return true;
            }
        }
    }
    //std::cout << "filter fov" << std::endl;
    return false;
}


bool FilterObjects::perceptionQuality(const LocalEnvironmentModel::TrackedObject& obj,
                               const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                               omnetpp::SimTime T_GenCpmDcc){

    const auto& vd = obj.first.lock()->getVehicleData();
    //double ratio = (mGenCpmMax - T_GenCpmDcc) / (mGenCpmMax - mGenCpmMin);
    double ratio = 0.75;

    //Range adaptation based on the quality level
    int nbSensorsThatDetected = 0;
    int maxNumberOfCornersDetected = 0;
    int nbCorners = 0;
    for(const auto& tracker : sensorsDetection) {

        if (tracker.first->getSensorCategory() == "Radar") {
            nbSensorsThatDetected++;
            nbCorners = obj.second.getQualityObservation().at(tracker.first);
            std::cout <<  "nbCorners: " << nbCorners << std::endl;
            if(nbCorners > maxNumberOfCornersDetected)
                maxNumberOfCornersDetected = nbCorners;
        }
    }

    std::cout << "nbSensorsThatDetected: " << nbSensorsThatDetected
                << " maxNumberOfCornersDetected: " << maxNumberOfCornersDetected << std::endl;

    if(ratio >= 0.85 ||
       (ratio >= 0.70 && maxNumberOfCornersDetected > 1) ||
       (ratio >= 0.60 && maxNumberOfCornersDetected > 1 && nbSensorsThatDetected > 1) ||
       (ratio >= 0.50 && maxNumberOfCornersDetected > 2 && nbSensorsThatDetected > 1)){
        std::cout << "pass" << std::endl;
        return true;
    }

    std::cout << "filter on perception" << std::endl;
    return false;
}


bool FilterObjects::updatingTime(const LocalEnvironmentModel::TrackedObject& obj,
                                                const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                                                Sensor * cpSensor, omnetpp::SimTime T_GenCpmDcc,
                                                ObjectInfo::ObjectsReceivedMap& objReceived, omnetpp::SimTime T_now){

    const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();

    //Check that the object is detected by one of the local sensor and has already been perceived by someone
    if (objReceived.find(vd.station_id()) != objReceived.end()) {

        ObjectInfo &infoObjectAI = objReceived.at(vd.station_id());

        //Remove the entry if expired
        if (objReceived.at(vd.station_id()).getLastTrackingTime().last() +
                cpSensor->getValidityPeriod() < mVehicleDataProvider->updated()) {
            objReceived.erase(vd.station_id());
            return true;

        //Check if time since the object has been perceived higher than the one imposed
        }

        /*std::cout << "\n\nLast time received " << objReceived.at(vd.station_id()).getLastTrackingTime().last() << std::endl;
        std::cout << "DCC time " << T_GenCpmDcc << std::endl;
        std::cout << "Sum of both " << objReceived.at(vd.station_id()).getLastTrackingTime().last() + T_GenCpmDcc << std::endl;
        std::cout << "Vehicle update time " << mVehicleDataProvider->updated() << std::endl;
        bool result = objReceived.at(vd.station_id()).getLastTrackingTime().last() + T_GenCpmDcc > mVehicleDataProvider->updated();
        std::cout << "Result (true = discard); " << result << std::endl;
        */
        if (objReceived.at(vd.station_id()).getLastTrackingTime().last() + T_GenCpmDcc >
                   mVehicleDataProvider->updated()) {
            //std::cout << "Filter object "<< vd.station_id() << " at  " << T_now << " because of time update refusal" << std::endl;
            //std::cout << "Time update refusal at " << T_now << std::endl;
            return false;
        }
    }
    return true;
}


bool FilterObjects::etsiFilter(const LocalEnvironmentModel::TrackedObject& obj,
                               const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                               ObjectInfo::ObjectsTrackedMap& prevObjSent,
                               ObjectInfo::ObjectsReceivedMap& objReceived,
                               const SimTime& T_now){

    const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();

    //If the position of the object since last time it has been sent, refuse it
    if(prevObjSent.find(obj.first) != prevObjSent.end()) {
        ObjectInfo &infoObject = prevObjSent.at(obj.first);

        if (!(checkTimeDelta(infoObject.getLastTimeSent(), T_now) ||
              checkSpeedDelta(infoObject.getLastVelocity(), vd.speed()) ||
              checkPositionDelta(infoObject.getLastPosition(), vd.position()))){
            //std::cout << "Etsi: Filter object "<< vd.station_id() << std::endl;
            return false;
        }
    }
    return true;
}

} // namespace artery
