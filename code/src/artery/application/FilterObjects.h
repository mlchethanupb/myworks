

#ifndef ARTERY_FILTEROBJECTS_H
#define ARTERY_FILTEROBJECTS_H

#include "artery/utility/Geometry.h"
#include <artery/envmod/LocalEnvironmentModel.h>
#include "artery/application/ObjectInfo.h"
#include <vanetza/asn1/cam.hpp>
#include <vanetza/btp/data_interface.hpp>
#include <vanetza/units/angle.hpp>
#include <vanetza/units/velocity.hpp>
#include <omnetpp/simtime.h>

namespace artery
{
    //class CPService;

    class FilterObjects
    {
    public:

        FilterObjects();

        FilterObjects(const VehicleDataProvider*, LocalEnvironmentModel*, std::vector<bool>,
                      vanetza::units::Angle, vanetza::units::Length, vanetza::units::Velocity,
                      std::map<const Sensor*, Identifier_t>*, const omnetpp::SimTime&,
                      const omnetpp::SimTime&);

        void initialize(const VehicleDataProvider*, LocalEnvironmentModel*, std::vector<bool>,
                          vanetza::units::Angle, vanetza::units::Length, vanetza::units::Velocity,
                          std::map<const Sensor*, Identifier_t>*, const omnetpp::SimTime&,
                          const omnetpp::SimTime&);

        std::size_t filterObjects(ObjectInfo::ObjectsPercievedMap &, ObjectInfo::ObjectsPercievedMap &,
                           omnetpp::SimTime, Sensor *, ObjectInfo::ObjectsReceivedMap&, const omnetpp::SimTime& T_now);

        void changeDeltas(vanetza::units::Angle hd, vanetza::units::Length pd, vanetza::units::Velocity sd);

        void getObjToSendNoFilter(ObjectInfo::ObjectsPercievedMap &objToSend, bool removeLowDynamics,
                ObjectInfo::ObjectsPercievedMap objectsPrevSent, const omnetpp::SimTime& T_now);

        ObjectInfo::ObjectsPercievedMap getallPercievedObjs();
        bool checkobjDynamics(const ObjectInfo::ObjectPercieved& obj, ObjectInfo::ObjectsPercievedMap&, omnetpp::SimTime T_now);

    private:

        const VehicleDataProvider* mVehicleDataProvider;
        const LocalEnvironmentModel* mLocalEnvironmentModel;
        std::vector<bool> mFiltersEnabled;
        vanetza::units::Angle mHeadingDelta;
        vanetza::units::Length mPositionDelta;
        vanetza::units::Velocity mSpeedDelta;
        omnetpp::SimTime mTimeDelta;
        std::map<const Sensor*, Identifier_t>* mSensorsId;
        omnetpp::SimTime mGenCpmMin;
        omnetpp::SimTime mGenCpmMax;


        bool checkHeadingDelta(vanetza::units::Angle, vanetza::units::Angle) const;
        bool checkPositionDelta(Position, Position) const;
        bool checkSpeedDelta(vanetza::units::Velocity,  vanetza::units::Velocity) const;
        bool checkTimeDelta(omnetpp::SimTime T_prev, omnetpp::SimTime T_now) const;

        bool v2xCapabilities(const LocalEnvironmentModel::TrackedObject&,
                            const LocalEnvironmentModel::Tracking::TrackingMap&,
                            ObjectInfo::ObjectsReceivedMap&);


        bool objectDynamicsLocal(const LocalEnvironmentModel::TrackedObject& ,
                                const LocalEnvironmentModel::Tracking::TrackingMap&,
                                ObjectInfo::ObjectsPercievedMap&, omnetpp::SimTime T_now);

        bool objectDynamicsV2X(const LocalEnvironmentModel::TrackedObject&,
                              const LocalEnvironmentModel::Tracking::TrackingMap&,
                              Sensor * cpSensor, omnetpp::SimTime,
                              ObjectInfo::ObjectsReceivedMap&);


        bool fovSensors(const LocalEnvironmentModel::TrackedObject&,
                         const LocalEnvironmentModel::Tracking::TrackingMap&,
                         omnetpp::SimTime);


        bool perceptionQuality(const LocalEnvironmentModel::TrackedObject&,
                                              const LocalEnvironmentModel::Tracking::TrackingMap&,
                                              omnetpp::SimTime);


        bool updatingTime(const LocalEnvironmentModel::TrackedObject& ,
                         const LocalEnvironmentModel::Tracking::TrackingMap&,
                         Sensor *, omnetpp::SimTime,
                         ObjectInfo::ObjectsReceivedMap&, omnetpp::SimTime T_now);

        bool etsiFilter(const LocalEnvironmentModel::TrackedObject& obj,
                       const LocalEnvironmentModel::Tracking::TrackingMap& sensorsDetection,
                       ObjectInfo::ObjectsPercievedMap& prevObjSent,
                       ObjectInfo::ObjectsReceivedMap& objReceived,
                       const omnetpp::SimTime& T_now);

    };

} // namespace artery



#endif //ARTERY_FILTEROBJECTS_H
