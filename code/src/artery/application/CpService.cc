/*
* Artery V2X Simulation Framework
* Copyright 2014-2019 Raphael Riebl et al.
* Licensed under GPLv2, see COPYING file for detailed license and warranty terms.
*/

//#include "artery/application/CaObject.h"
#include "artery/application/CpObject.h"
#include "artery/application/CpService.h"
#include "artery/application/Configurations.h"
#include "artery/application/Asn1PacketVisitor.h"
#include "artery/application/MultiChannelPolicy.h"
#include "artery/application/VehicleDataProvider.h"
#include "artery/envmod/sensor/SensorPosition.h"
#include "artery/envmod/LocalEnvironmentModel.h"
#include "artery/envmod/EnvironmentModelObject.h"
#include "artery/inet/InetMobility.h"
#include "artery/utility/simtime_cast.h"
#include "veins/base/utils/Coord.h"
#include <boost/units/cmath.hpp>
#include <boost/units/systems/si/prefixes.hpp>
#include <omnetpp/cexception.h>
#include <vanetza/btp/ports.hpp>
#include <vanetza/dcc/transmission.hpp>
#include <vanetza/dcc/transmit_rate_control.hpp>
#include <vanetza/facilities/cam_functions.hpp>
#include <chrono>

// #define COMPILE_CODE

namespace artery
{

using namespace omnetpp;


static const simsignal_t scSignalCpmReceived = cComponent::registerSignal("CpmReceived");
static const simsignal_t scSignalCpmSent = cComponent::registerSignal("CpmSent");
static const simsignal_t scSignalEteDelay = cComponent::registerSignal("EteDelay");
static const simsignal_t scSignalRatioObjectAge = cComponent::registerSignal("objectAge");


static const auto scSnsrInfoContainerInterval = std::chrono::milliseconds(1000);

const auto DCCPROFILECP = vanetza::dcc::Profile::DP2;
const size_t MAXCPMSIZE = 1100;

Define_Module(CpService)

CpService::CpService():
		mGenCpmMin { 100, SIMTIME_MS },
		mGenCpmMax { 1000, SIMTIME_MS },
		mGenCpm(mGenCpmMax),
		mGenCpmLowDynamicsCounter(0),
		mGenCpmLowDynamicsLimit(3)
{
}

void CpService::initialize()
{
	ItsG5BaseService::initialize();
	mNetworkInterfaceTable = &getFacilities().get_const<NetworkInterfaceTable>();
	mVehicleDataProvider = &getFacilities().get_const<VehicleDataProvider>();
	mTimer = &getFacilities().get_const<Timer>();
	mLocalDynamicMap = &getFacilities().get_mutable<artery::LocalDynamicMap>();
	mLocalEnvironmentModel = &getFacilities().get_mutable<LocalEnvironmentModel>();

	// avoid unreasonable high elapsed time values for newly inserted vehicles
	mLastCpmTimestamp = simTime();

	// first generated CPM shall include the sensor information container
	mLastSenrInfoCntnrTimestamp = mLastCpmTimestamp - artery::simtime_cast(scSnsrInfoContainerInterval);

	// generation rate boundaries
	mGenCpmMin = par("minInterval");
	mGenCpmMax = par("maxInterval");


	// vehicle dynamics thresholds
	mHeadingDelta = vanetza::units::Angle { par("headingDelta").doubleValue() * vanetza::units::degree };
	mPositionDelta = par("positionDelta").doubleValue() * vanetza::units::si::meter;
	mSpeedDelta = par("speedDelta").doubleValue() * vanetza::units::si::meter_per_second;

	//mDccRestriction = par("withDccRestriction");
	mFixedRate = par("fixedRate");

	mPrimaryChannel = getFacilities().get_const<MultiChannelPolicy>().primaryChannel(vanetza::aid::CP);

	if(mSensorsId.empty()){
		generate_sensorid();
	}
    // Objects filters
    /*
	mFiltersEnabled = std::vector<bool>{par("v2xCapabilities"), par("objectDynamicsLocal"),
                                        par("objectDynamicsV2X"),
                                        par("fovSensors"), par("perceptionQuality"), par("updatingTime"),
                                        par("etsiFilter")};
	*/
	mFiltersEnabled = std::vector<bool>{true, true, true, true, true, true, true};

    mFilterObj.initialize(mVehicleDataProvider, mLocalEnvironmentModel, mFiltersEnabled, mHeadingDelta,
                          mPositionDelta, mSpeedDelta, &mSensorsId, mGenCpmMin, mGenCpmMax);
}

void CpService::trigger()
{
	Enter_Method("trigger");
    std::cout << "mVehicleDataProvider->updated(): " << mVehicleDataProvider->updated() << ", simTime(): " << simTime() << std::endl; 

	generateCPM(simTime());

    //Statistics
    recordObjectsAge();
}

void CpService::indicate(const vanetza::btp::DataIndication& ind, std::unique_ptr<vanetza::UpPacket> packet)
{

	Enter_Method("indicate");

	EV<< "CPM message received" << endl;
    std::cout << "CPM message received" << endl;

	if(mSensorsId.empty()){
		generate_sensorid();
	}

	Asn1PacketVisitor<vanetza::asn1::Cpm> visitor;
	const vanetza::asn1::Cpm* cpm = boost::apply_visitor(visitor, *packet);
	if (cpm && cpm->validate()) {

		CpObject obj = visitor.shared_wrapper;

        std::cout << "publishing signal cpm received" << std::endl;
		emit(scSignalCpmReceived, &obj);

		const vanetza::asn1::Cpm& cpm_msg = obj.asn1();
		retrieveCPMmessage(cpm_msg);
		printCPM(cpm_msg);

	}else{
        std::cout << "cpm object: " << cpm << endl;
    }
}

bool CpService::checkHeadingDelta() const
{
	return !vanetza::facilities::similar_heading(mLastCpmHeading, mVehicleDataProvider->heading(), mHeadingDelta);
}

bool CpService::checkPositionDelta() const
{
	return (distance(mLastCpmPosition, mVehicleDataProvider->position()) > mPositionDelta);
}

bool CpService::checkSpeedDelta() const
{
	return abs(mLastCpmSpeed - mVehicleDataProvider->speed()) > mSpeedDelta;
}

void CpService::generateCPM(const omnetpp::SimTime& T_now) {

	// provide variables named like in TR 103 562 V0.0.16 (section 4.3.4)
	SimTime& T_GenCpm = mGenCpm;
	const SimTime& T_GenCpmMin = mGenCpmMin;
	const SimTime& T_GenCpmMax = mGenCpmMax;
	const SimTime T_elapsed = T_now - mLastCpmTimestamp;

/*	if (T_elapsed >= T_GenCpm) {
		sendCpm(T_now);			
	}*/
	if (T_elapsed >= T_GenCpmMax) { //T_GenCpmDcc to be used??
		if (mFixedRate) {
			sendCpm(T_now);
		} else if (checkHeadingDelta() || checkPositionDelta() || checkSpeedDelta()) {
			sendCpm(T_now);
			T_GenCpm = std::min(T_elapsed, T_GenCpmMax); /*< if middleware update interval is too long */
			mGenCpmLowDynamicsCounter = 0;
		} else if (T_elapsed >= T_GenCpm) {
			sendCpm(T_now);
			if (++mGenCpmLowDynamicsCounter >= mGenCpmLowDynamicsLimit) {
				T_GenCpm = T_GenCpmMax;
			}
		}
	}
}

void CpService::sendCpm(const omnetpp::SimTime& T_now) {

	EV <<"Generating collective perception message for vehicle: " << mVehicleDataProvider->station_id() << endl;
    //std::cout <<"Generating collective perception message for vehicle: " << mVehicleDataProvider->station_id() << endl;

	if(mSensorsId.empty()){
		generate_sensorid();
	}

	bool snsrcntr_prsnt = false;
	bool prcvdobjcntr_prsnt = false;

	vanetza::asn1::Cpm cpm_msg;

	ItsPduHeader_t& header = (*cpm_msg).header;
	header.protocolVersion = 1;
	header.messageID = ItsPduHeader__messageID_cpm;
	header.stationID = mVehicleDataProvider->station_id();

	CollectivePerceptionMessage_t& cpm = (*cpm_msg).cpm;

	uint16_t genDeltaTime = countTaiMilliseconds(mTimer->getTimeFor(mVehicleDataProvider->updated()));
	cpm.generationDeltaTime = genDeltaTime * GenerationDeltaTime_oneMilliSec;

	if(T_now - mLastSenrInfoCntnrTimestamp >= SimTime(1, SIMTIME_S)){
		EV << "Generating sensor objects" << std::endl;
		snsrcntr_prsnt = generateSensorInfoCntnr(cpm_msg);
		if(snsrcntr_prsnt){
			mLastSenrInfoCntnrTimestamp = T_now;
		}
	} 
	
	prcvdobjcntr_prsnt = generatePerceivedObjectsCntnr(cpm_msg, T_now);
	//generate_objlist(cpm_msg, T_now);
	
	if(prcvdobjcntr_prsnt || snsrcntr_prsnt ) {
		generateStnAndMgmtCntnr(cpm_msg);
	} 

	using namespace vanetza;
	btp::DataRequestB request;
	request.destination_port = btp::ports::CPM;
	request.gn.its_aid = aid::CP;
	request.gn.transport_type = geonet::TransportType::SHB;
	request.gn.maximum_lifetime = geonet::Lifetime { geonet::Lifetime::Base::One_Second, 1 };
	request.gn.traffic_class.tc_id(static_cast<unsigned>(dcc::Profile::DP2));
	request.gn.communication_profile = geonet::CommunicationProfile::ITS_G5; //@todo: LTE-V2X ?


	CpObject obj(std::move(cpm_msg));
	emit(scSignalCpmSent, &obj);

	using CpmByteBuffer = convertible::byte_buffer_impl<asn1::Cpm>;
	std::unique_ptr<geonet::DownPacket> payload { new geonet::DownPacket() };
	std::unique_ptr<convertible::byte_buffer> buffer { new CpmByteBuffer(obj.shared_ptr()) };
	payload->layer(OsiLayer::Application) = std::move(buffer);
	this->request(request, std::move(payload));
}

bool CpService::generatePerceivedObjectsCntnr(vanetza::asn1::Cpm& cpm_msg, const omnetpp::SimTime& T_now){

	//get all the prcd object list
	ObjectInfo::ObjectsPercievedMap prcvd_objs = mFilterObj.getallPercievedObjs();

	//No objects percieved by the sensors
	/*if(prcvd_objs.empty()){
		return false;
	}*/
		
    //std::cout << "objs perceived count: " << prcvd_objs.size() << endl;

	for(const ObjectInfo::ObjectPercieved& p_obj : prcvd_objs){

		//@todo check for the confidence level

		//check in tracking list
		if(objinTrackedlist(p_obj)){

			//@todo: check for the object belonging to class person or animal

			//check the dynamics and time elapsed of the object
			if(mFilterObj.checkobjectDynamics(p_obj, mObjectsTracked, T_now)){
				mObjectsToSend.insert(p_obj);
			}
		}
	}

	generateASN1Objects(cpm_msg, T_now, mObjectsToSend);
    checkCPMSize(T_now, mObjectsToSend, cpm_msg);

    //Add object in the list of previously sent
    updateObjTrackedList(T_now, mObjectsToSend);

	return true;
}

//check if the object already in the tracked list?
bool CpService::objinTrackedlist(const ObjectInfo::ObjectPercieved& obj){

	if (mObjectsTracked.find(obj.first) != mObjectsTracked.end()) {
		return true;
    } else {
		//if its new object select add to the object tracking list and also the to object sender list. 
		mObjectsToSend.insert(obj);
		mObjectsTracked.insert(obj);
		return false;
    }
}

void CpService::generate_objlist(vanetza::asn1::Cpm &message, const omnetpp::SimTime& T_now){

    mObjectsToSend.clear();
    std::size_t countObject = mFilterObj.filterObjects(mObjectsToSend, mObjectsTracked, genCpmDcc(), mCPSensor,
                                                           mObjectsReceived, T_now);

    generateASN1Objects(message, T_now, mObjectsToSend);
    checkCPMSize(T_now, mObjectsToSend, message);

    //Add object in the list of previously sent
    updateObjTrackedList(T_now, mObjectsToSend);

    //EV << "Send CPM with " << objectsToSend.size() << " objects" << std::endl;
    double nbRadarObj = (double) boost::size(filterBySensorCategory(mLocalEnvironmentModel->allObjects(), "Radar"));



    //if (nbRadarObj != 0)
        //emit(scSignalRatioFilter, (double) 1 - (double) mObjectsToSend.size() / nbRadarObj);

}

void CpService::generateASN1Objects(vanetza::asn1::Cpm &message, const omnetpp::SimTime &T_now,
                                    ObjectInfo::ObjectsPercievedMap objToSend) {

    //TODO: check for memory leaking here
    PerceivedObjectContainer_t *& perceivedObjectContainers = (*message).cpm.cpmParameters.perceivedObjectContainer;
    vanetza::asn1::free(asn_DEF_PerceivedObjectContainer, perceivedObjectContainers);
    perceivedObjectContainers = nullptr;

    if (!objToSend.empty()) {
        perceivedObjectContainers = vanetza::asn1::allocate<PerceivedObjectContainer_t>();
        for (auto &obj : objToSend) {
            //if (obj.first.expired()) continue;
            PerceivedObject_t *objContainer = createPerceivedObjectContainer(obj.first, obj.second);
            ASN_SEQUENCE_ADD(perceivedObjectContainers, objContainer);
        }
	}else{
		EV_INFO << "MLC ----- No objects to send" << std::endl;
	}
#ifdef REMOVE_CODE
	if(perceivedObjectContainers->list.count == 0){
		vanetza::asn1::free(asn_DEF_PerceivedObjectContainer, perceivedObjectContainers);
    	perceivedObjectContainers = nullptr;
		std::cout << "entered" << std::endl;
	}
#endif
}

PerceivedObject_t *
CpService::createPerceivedObjectContainer(const std::weak_ptr<artery::EnvironmentModelObject> &object,
                                          ObjectInfo &infoObj) {

    const auto &vdObj = object.lock()->getVehicleData();

    PerceivedObject_t *objContainer = vanetza::asn1::allocate<PerceivedObject_t>();

    objContainer->objectID = vdObj.station_id();

    //@todo - add later
	//objContainer->sensorIDList = new Identifier_t(infoObj.getSensorId());

    //Compute relative time between CPM generation and time of observation of the object
    //std::cout << "Time perception:" << (uint16_t) countvoid CPService::checkCPMSize(const SimTime& T_now, ObjectInfo::ObjectsPercievedMap& objToSend, vanetza::asn1::Cpm& cpm)ong>(cpm.generationDeltaTime,
     //                                                         (u_int16_t) countTaiMilliseconds(mTimer->getTimeFor(
      //                                                                infoObj.getLastTrackingTime().last())),
       //                                                       TIMEOFMEASUREMENTMAX, GENERATIONDELTATIMEMAX);

    //Need to give relative position because the relative position is between (-132768..132767) cm
    //Change axis y from south to north
    objContainer->xDistance.value =
            ((vdObj.position().x - mVehicleDataProvider->position().x) / boost::units::si::meter) *
            DistanceValue_oneMeter;
    objContainer->xDistance.confidence = DistanceConfidence_oneMeter;
    objContainer->yDistance.value =
            -((vdObj.position().y - mVehicleDataProvider->position().y) / boost::units::si::meter) *
            DistanceValue_oneMeter;
    objContainer->yDistance.confidence = DistanceConfidence_oneMeter;

    /** @note: prevent teleportation **/
    if(abs(objContainer->xDistance.value) > 132767 || abs(objContainer->yDistance.value) > 132767){
        objContainer->xDistance.value = 0;
        objContainer->yDistance.value = 0;
    }


    /** @note xSpeed and ySpeed should be computed relatively to the ego speed. For simplicity, we consider the
     * speed of the vehicle detected directly.
     */
    const inet::Coord direction{sin(vdObj.heading()), cos(vdObj.heading())};
    inet::Coord speed =
            direction * (vdObj.speed() / vanetza::units::si::meter_per_second) * 100; //Conversion in cm/s
    objContainer->xSpeed.value = speed.x;
    objContainer->xSpeed.confidence = SpeedConfidence_equalOrWithinOneMeterPerSec;
    objContainer->ySpeed.value = speed.y;
    objContainer->ySpeed.confidence = SpeedConfidence_equalOrWithinOneMeterPerSec;

    if(abs(objContainer->xSpeed.value) > 16383 || abs(objContainer->ySpeed.value) > 16383){
        objContainer->xSpeed.value = 0;
        objContainer->ySpeed.value = 0;

    }

    objContainer->planarObjectDimension1 = vanetza::asn1::allocate<ObjectDimension_t>();
    objContainer->planarObjectDimension1->value =
            object.lock()->getLength() / boost::units::si::meter * ObjectDimensionValue_oneMeter;
    objContainer->planarObjectDimension1->confidence = 0;

    objContainer->planarObjectDimension2 = vanetza::asn1::allocate<ObjectDimension_t>();
    objContainer->planarObjectDimension2->value =
            object.lock()->getWidth() / boost::units::si::meter * ObjectDimensionValue_oneMeter;
    objContainer->planarObjectDimension2->confidence = 0;

    objContainer->dynamicStatus = vanetza::asn1::allocate<DynamicStatus_t>();
    *(objContainer->dynamicStatus) = DynamicStatus_dynamic;

	//@todo - convert to the list
    //objContainer->classification = vanetza::asn1::allocate<StationType_t>();
    //*(objContainer->classification) = StationType_passengerCar;

    return objContainer;
}


void CpService::updateObjTrackedList(const omnetpp::SimTime& T_now, ObjectInfo::ObjectsPercievedMap objToSend){
    //Add object in the list of previously sent
    for(auto obj : objToSend) {
        obj.second.setLastTimeSent(T_now);
        if (mObjectsTracked.find(obj.first) != mObjectsTracked.end()) {
            mObjectsTracked[obj.first] = obj.second;
        } else {
            mObjectsTracked.insert(obj);
        }
    }
}

void CpService::checkCPMSize(const SimTime& T_now, ObjectInfo::ObjectsPercievedMap& objToSend, vanetza::asn1::Cpm& cpm){
	bool removedObject = false;
	while(cpm.size() > MAXCPMSIZE){
		ObjectInfo::ObjectsPercievedMap::iterator item = objToSend.begin();
		std::advance(item, std::rand() % objToSend.size());
		objToSend.erase(item);
		generateASN1Objects(cpm, T_now, objToSend);
		removedObject = true;
	}

	//if(removedObject)
	//	emit(scSignalRemovedObjExcessiveSize, 1);
}

void CpService::generate_sensorid(){

	std::vector<Sensor*> sensors = mLocalEnvironmentModel->allSensors();

	//Check that at least some sensors are available and that some of them are for perception, i.e., radar.
    if (sensors.size() == 0 || boost::size(filterBySensorCategory(mLocalEnvironmentModel->allObjects(), "Radar")) == 0){
        EV_WARN << "No sensors for local perception currently used along the CP service" << std::endl;
	}

    for (int i = 0; i < sensors.size(); i++) {
        
        //std::cout << "sensor category: " << sensors[i]->getSensorCategory() << std::endl;

        mSensorsId.insert(std::pair<Sensor *, Identifier_t>(sensors[i], i));
      
        if (!mCPSensor && sensors[i]->getSensorCategory() == "CP")
            mCPSensor = sensors[i];

        if (!mCASensor && sensors[i]->getSensorCategory() == "CA")
            mCASensor = sensors[i];
    }
}

void CpService::addsensorinfo(SensorInformationContainer_t *& snsrinfo_cntr, Sensor*& sensor, SensorType_t sensorType){

	if(snsrinfo_cntr){


		SensorInformation_t* snsr_info =  vanetza::asn1::allocate<SensorInformation_t>();

		snsr_info->sensorID = mSensorsId.at(sensor);
		snsr_info->type = sensorType;
		snsr_info->detectionArea.present = DetectionArea_PR_vehicleSensor;
		
		//std::cout << "adding sensor information " << snsr_info->sensorID << std::endl;

		VehicleSensor_t& vehicle_snsr =  snsr_info->detectionArea.choice.vehicleSensor;

		std::pair<long, long> positionPair = artery::relativePosition(sensor->position());

		vehicle_snsr.refPointId = 0;
		vehicle_snsr.xSensorOffset = positionPair.first;
		vehicle_snsr.ySensorOffset = positionPair.second;
		
		//In our case only add 1 vehicle sensor properties for each sensor
		VehicleSensorProperties_t* vhcleSnsrProp =  vanetza::asn1::allocate<VehicleSensorProperties_t>();

		vhcleSnsrProp->range = sensor->getFieldOfView()->range.value() * Range_oneMeter;
		const double openingAngleDeg = sensor->getFieldOfView()->angle / boost::units::degree::degrees;
    	const double sensorPositionDeg = artery::relativeAngle(sensor->position()) / boost::units::degree::degrees;

		 //angle anti-clockwise
    	vhcleSnsrProp->horizontalOpeningAngleStart = std::fmod(std::fmod((sensorPositionDeg - 0.5 * openingAngleDeg), 
													 (double) 360) + 360, 360) * CartesianAngleValue_oneDegree;
    	vhcleSnsrProp->horizontalOpeningAngleEnd = std::fmod(std::fmod((sensorPositionDeg + 0.5 * openingAngleDeg), 
												   (double) 360) + 360, 360) * CartesianAngleValue_oneDegree;

		int result = ASN_SEQUENCE_ADD(&vehicle_snsr.vehicleSensorPropertyList, vhcleSnsrProp);
		if (result != 0) {
			perror("asn_set_add() failed");
			exit(EXIT_FAILURE);
		}

		result = ASN_SEQUENCE_ADD(snsrinfo_cntr, snsr_info);
		if (result != 0) {
			perror("asn_set_add() failed");
			exit(EXIT_FAILURE);
		}
		
	}else{
		EV_WARN << "Sensor Information container is not initialized" << std::endl;
	}

}

bool CpService::generateSensorInfoCntnr(vanetza::asn1::Cpm& cpm_msg){

	SensorInformationContainer_t*& snsrinfo_cntr =  (*cpm_msg).cpm.cpmParameters.sensorInformationContainer;
	snsrinfo_cntr = vanetza::asn1::allocate<SensorInformationContainer_t>();

	std::vector<Sensor*> sensors = mLocalEnvironmentModel->allSensors();

    for (int i = 0; i < sensors.size(); i++) {
        if (sensors[i]->getSensorCategory() == "Radar") {
            addsensorinfo(snsrinfo_cntr, sensors[i],SensorType_radar);
        }
    }
 	return true;
}

bool CpService::generateStnAndMgmtCntnr(vanetza::asn1::Cpm& cpm_msg){

	if( vanetza::geonet::StationType::Passenger_Car == mVehicleDataProvider->getStationType()){
		generateCarStnCntnr(cpm_msg);

	}else if(vanetza::geonet::StationType::RSU == mVehicleDataProvider->getStationType()){
		// @todo: add check to see if ITS-S disseminate the MAP-message
		// assemble the originating RSU container
		generateRSUStnCntnr(cpm_msg);
	}
	
	generateMgmtCntnr(cpm_msg);
	
	//@todo: steps to handle the segmentation
	return true;
}

void CpService::generateMgmtCntnr(vanetza::asn1::Cpm& cpm_msg){

	CpmManagementContainer_t& mngmtCntnr = (*cpm_msg).cpm.cpmParameters.managementContainer;
	
	mngmtCntnr.stationType = static_cast<StationType_t>(mVehicleDataProvider->getStationType());

	mngmtCntnr.referencePosition.altitude.altitudeValue = AltitudeValue_unavailable;
	mngmtCntnr.referencePosition.altitude.altitudeConfidence = AltitudeConfidence_unavailable;
	mngmtCntnr.referencePosition.longitude = artery::config::round(mVehicleDataProvider->longitude(), artery::config::microdegree) * Longitude_oneMicrodegreeEast;
	mngmtCntnr.referencePosition.latitude = artery::config::round(mVehicleDataProvider->latitude(), artery::config::microdegree) * Latitude_oneMicrodegreeNorth;
	mngmtCntnr.referencePosition.positionConfidenceEllipse.semiMajorOrientation = HeadingValue_unavailable;
	mngmtCntnr.referencePosition.positionConfidenceEllipse.semiMajorConfidence = SemiAxisLength_unavailable;
	mngmtCntnr.referencePosition.positionConfidenceEllipse.semiMinorConfidence = SemiAxisLength_unavailable;
}

void CpService::generateCarStnCntnr(vanetza::asn1::Cpm& cpm_msg){

	StationDataContainer_t*& stndata =  (*cpm_msg).cpm.cpmParameters.stationDataContainer;
	stndata = vanetza::asn1::allocate<StationDataContainer_t>();

	stndata->present = StationDataContainer_PR_originatingVehicleContainer;

	OriginatingVehicleContainer_t& orgvehcntnr = stndata->choice.originatingVehicleContainer;
	orgvehcntnr.heading.headingValue = artery::config::round(mVehicleDataProvider->heading(), artery::config::decidegree);
	orgvehcntnr.heading.headingConfidence =  HeadingConfidence_equalOrWithinOneDegree;
	orgvehcntnr.speed.speedValue = artery::config::buildSpeedValue(mVehicleDataProvider->speed());
	orgvehcntnr.speed.speedConfidence = SpeedConfidence_equalOrWithinOneCentimeterPerSec * 3;
	orgvehcntnr.driveDirection = mVehicleDataProvider->speed().value() >= 0.0 ? DriveDirection_forward : DriveDirection_backward;
}

void CpService::generateRSUStnCntnr(vanetza::asn1::Cpm& cpm_msg){

	StationDataContainer_t*& stndata =  (*cpm_msg).cpm.cpmParameters.stationDataContainer;
	stndata = vanetza::asn1::allocate<StationDataContainer_t>();

	stndata->present = StationDataContainer_PR_originatingRSUContainer;
}

void CpService::retrieveCPMmessage(const vanetza::asn1::Cpm& cpm_msg){

	EV <<" CPM message received by "<< mVehicleDataProvider->station_id() <<", retriving information "<< endl;

    const CPM_t cpm = (*cpm_msg);
	const CPM_t* cpm_data = &cpm;
    //Get info of the emitter vehicle
    uint32_t stationID = cpm_data->header.stationID;
    omnetpp::SimTime generationTime = mTimer->getTimeFor(
            mTimer->reconstructMilliseconds(cpm_data->cpm.generationDeltaTime));

    omnetpp::SimTime ete_delay = mVehicleDataProvider->updated() - generationTime;
    emit(scSignalEteDelay, ete_delay);

    if (mObjectsReceived.find(stationID) == mObjectsReceived.end() || //First time object perceived
        mObjectsReceived.at(stationID).getLastTrackingTime().last() + mCPSensor->getValidityPeriod() <= simTime() ||
        //Object is expired
        generationTime > mObjectsReceived.at(stationID).getLastTrackingTime().last()) { // the CPM received is more recent


        OriginatingVehicleContainer_t originVeh = cpm_data->cpm.cpmParameters.stationDataContainer->choice.originatingVehicleContainer;
        LocalEnvironmentModel::TrackingTime newTracking(generationTime);

        //Retrieve heading, position and velocity
        vanetza::units::Angle headingReceived(originVeh.heading.headingValue * config::decidegree);

        /** @note For simplicity, in management container, the position (x,y) is given instead of (longitude, latitude) */
        Position posReceivedStation(
                (double) cpm_data->cpm.cpmParameters.managementContainer.referencePosition.longitude /
                DistanceValue_oneMeter,
                -(double) cpm_data->cpm.cpmParameters.managementContainer.referencePosition.latitude /
                DistanceValue_oneMeter);

        vanetza::units::Velocity speedReceived(originVeh.speed.speedValue * config::centimeter_per_second);

		EV << "MLC--- station id: " << stationID << std::endl;
        mObjectsReceived[stationID] = ObjectInfo(newTracking,  mSensorsId.at(mCPSensor), headingReceived,  posReceivedStation, speedReceived);
      
    }

    #if 1
    //Get info of the objects received:
    PerceivedObjectContainer_t *objectsContainer = cpm_data->cpm.cpmParameters.perceivedObjectContainer;
    for (int i = 0; objectsContainer != nullptr && i < objectsContainer->list.count; i++) {

        PerceivedObject_t *objCont = objectsContainer->list.array[i];

        /** @note Skip message received about myself */
        if (objCont->objectID == mVehicleDataProvider->station_id()) {
            continue;
        }

        omnetpp::SimTime objectPerceptTime = mTimer->getTimeFor(mTimer->reconstructMilliseconds(
                cpm_data->cpm.generationDeltaTime - objCont->timeOfMeasurement));

        if (mObjectsReceived.find(objCont->objectID) == mObjectsReceived.end() || //First time object perceived
            mObjectsReceived.at(objCont->objectID).getLastTrackingTime().last() + mCPSensor->getValidityPeriod() <= simTime() || //Object is expired
            objectPerceptTime > mObjectsReceived.at(
                    objCont->objectID).getLastTrackingTime().last()) { // the CPM received is more recent

            LocalEnvironmentModel::TrackingTime newTracking(objectPerceptTime);

            vanetza::units::Velocity speedX(objCont->xSpeed.value * config::centimeter_per_second);
            vanetza::units::Velocity speedY(objCont->ySpeed.value * config::centimeter_per_second);

            vanetza::units::Angle headingReceived = VehicleDataProvider::computeHeading(speedX, speedY);

            bool headingAvalaible = headingReceived != -1 * vanetza::units::si::radian;

            /** @note Change the axis to point to the south (OMNeT++ frame) */
            ReferencePosition_t refPosSender = cpm_data->cpm.cpmParameters.managementContainer.referencePosition;

            Position posReceived(
                    ((double) objCont->xDistance.value + refPosSender.longitude) / DistanceValue_oneMeter,
                    -((double) objCont->yDistance.value + refPosSender.latitude) / DistanceValue_oneMeter);

            vanetza::units::Velocity speedReceived = boost::units::sqrt(
                    boost::units::pow<2>(speedX) + boost::units::pow<2>(speedY));

            if (mObjectsReceived.find(objCont->objectID) == mObjectsReceived.end()) {

                mObjectsReceived[objCont->objectID] = ObjectInfo(newTracking, mSensorsId.at(mCPSensor),
                                                                 headingReceived, posReceived,
                                                                 speedReceived); 
            } else {
                
                mObjectsReceived[objCont->objectID] = ObjectInfo(
                        newTracking, mSensorsId.at(mCPSensor), headingReceived,
                        posReceived, speedReceived);
            }
        }
    }
    #endif

}

SimTime CpService::genCpmDcc() {
    // network interface may not be ready yet during initialization, so look it up at this later point
    auto netifc = mNetworkInterfaceTable->select(mPrimaryChannel);
    vanetza::dcc::TransmitRateThrottle *trc = netifc ? netifc->getDccEntity().getTransmitRateThrottle() : nullptr;
    if (!trc) {
        throw cRuntimeError("No DCC TRC found for CP's primary channel %i", mPrimaryChannel);
    }
    static const vanetza::dcc::TransmissionLite cp_tx(DCCPROFILECP, 0);
    vanetza::Clock::duration delay = trc->interval(cp_tx);
    SimTime dcc{std::chrono::duration_cast<std::chrono::milliseconds>(delay).count(), SIMTIME_MS};
    //TODO revove
    //std::cout << "time to wait before next transmission: " << dcc << std::endl;
    return std::min(mGenCpmMax, std::max(mGenCpmMin, dcc));
}



void CpService::recordObjectsAge(){

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

		if(!detectedByRadars){
			const VehicleDataProvider &vd = obj.first.lock()->getVehicleData();

			if (mObjectsReceived.find(vd.station_id()) != mObjectsReceived.end()) {
				ObjectInfo &infoObjectAI = mObjectsReceived.at(vd.station_id());

				//Remove the entry if expired
				if (mObjectsReceived.at(vd.station_id()).getLastTrackingTime().last() +
					mCPSensor->getValidityPeriod() < mVehicleDataProvider->updated()) {
					mObjectsReceived.erase(vd.station_id());
				} else {
                    emit(scSignalRatioObjectAge, simTime() - mObjectsReceived.at(vd.station_id()).getLastTrackingTime().last());
                }
			}
		}
	}
}
/** Print information of a CPM message
 * @param CPM struct from asnc
 * @return /
 */
void CpService::printCPM(const vanetza::asn1::Cpm &message) {
        const CPM_t &cpm = (*message);

        EV << "\n--- CPM at: " << simTime() << " ---" << std::endl;
        //Print header
        EV << "Header:\n\tprotocolVersion: " << cpm.header.protocolVersion
                  << "\n\tmessageID: " << cpm.header.messageID << "\n\tstationID: " << cpm.header.stationID
                  << std::endl;

        //Generation delta time
        EV << "generationDeltaTime: " << cpm.cpm.generationDeltaTime << std::endl;

        //CPM parameters
        EV << "-- CpmParameters --" << std::endl;

        //Management container
        CpmManagementContainer_t cpmManag = cpm.cpm.cpmParameters.managementContainer;
        EV << "CpmManagementContainer:\n\tstationType: " << cpmManag.stationType
                  << "\n\treferencePosition:\n\t\tlongitude: " << cpmManag.referencePosition.longitude
                  << "\n\t\tlatitude: " << cpmManag.referencePosition.latitude << std::endl;

        //Station data container
        StationDataContainer_t *cpmStationDC = cpm.cpm.cpmParameters.stationDataContainer;
        if (cpmStationDC) {
            EV << "StationDataContainer:\n\ttype: vehicle (fixed)"
                      << "\n\theading: " << cpmStationDC->choice.originatingVehicleContainer.heading.headingValue
                      << "\n\tspeed: " << cpmStationDC->choice.originatingVehicleContainer.speed.speedValue
                      << std::endl;

        }

        //Sensors list:
        EV << "-- List of sensors --" << std::endl;
        SensorInformationContainer_t *sensorsContainer = cpm.cpm.cpmParameters.sensorInformationContainer;
        for (int i = 0; sensorsContainer != nullptr && i < sensorsContainer->list.count; i++) {
            SensorInformation_t *sensCont = sensorsContainer->list.array[i];
            EV << "Sensor " << i << ": \n\tId: " << sensCont->sensorID
                      << "\n\tType: " << sensCont->type;

			/*
            if (sensCont->details.present == SensorDetails_PR_vehicleSensor) {
                VehicleSensor_t sensDetails = sensCont->details.choice.vehicleSensor;

                EV << "\n\tReference point: " << sensDetails.refPointId
                          << "\n\tX Sensor offset: " << sensDetails.xSensorOffset
                          << "\n\tY Sensor offset: " << sensDetails.ySensorOffset;

                ListOfVehicleSensorProperties_t sensorProperties = sensDetails.vehicleSensorProperties;
                for (int j = 0; j < sensorProperties.list.count; j++) {
                    VehicleSensorProperties_t *sensProp = sensorProperties.list.array[j];
                    EV << "\n\tRange: " << sensProp->range / Range_oneMeter
                              << "\n\tHor. op. angle start: "
                              << sensProp->horizontalOpeningAngleStart / CartesianAngleValue_oneDegree
                              << "\n\tHor. op. angle end: "
                              << sensProp->horizontalOpeningAngleEnd / CartesianAngleValue_oneDegree;
                }
            }
			*/

            EV << std::endl << std::endl;
        }

        //Perceived object container
        EV << "-- List of Objects --" << std::endl;
        PerceivedObjectContainer_t *objectsContainer = cpm.cpm.cpmParameters.perceivedObjectContainer;
        for (int i = 0; objectsContainer != nullptr && i < objectsContainer->list.count; i++) {
            PerceivedObject_t *objCont = objectsContainer->list.array[i];
            EV << "Object " << i << ": \n\tobjectId: " << objCont->objectID
                      << "\n\ttimeOfMeasurement: " << objCont->timeOfMeasurement
                      << "\n\txDistance: " << objCont->xDistance.value
                      << "\n\tyDistance: " << objCont->yDistance.value
                      << "\n\txSpeed: " << objCont->xSpeed.value
                      << "\n\tySpeed: " << objCont->ySpeed.value
                      << std::endl << std::endl;
        }
    }
} // namespace artery
