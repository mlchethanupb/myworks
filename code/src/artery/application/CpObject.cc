#include <artery/application/CpObject.h>
#include <omnetpp.h>
#include <cassert>

namespace artery
{

using namespace vanetza::asn1;

Register_Abstract_Class(CpObject)

CpObject::CpObject(Cam&& cam) :
    m_cam_wrapper(std::make_shared<Cam>(std::move(cam)))
{
}

CpObject& CpObject::operator=(Cam&& cam)
{
    m_cam_wrapper = std::make_shared<Cam>(std::move(cam));
    return *this;
}

CpObject::CpObject(const Cam& cam) :
    m_cam_wrapper(std::make_shared<Cam>(cam))
{
}

CpObject& CpObject::operator=(const Cam& cam)
{
    m_cam_wrapper = std::make_shared<Cam>(cam);
    return *this;
}

CpObject::CpObject(const std::shared_ptr<const Cam>& ptr) :
    m_cam_wrapper(ptr)
{
    assert(m_cam_wrapper);
}

CpObject& CpObject::operator=(const std::shared_ptr<const Cam>& ptr)
{
    m_cam_wrapper = ptr;
    assert(m_cam_wrapper);
    return *this;
}

std::shared_ptr<const Cam> CpObject::shared_ptr() const
{
    assert(m_cam_wrapper);
    return m_cam_wrapper;
}

const vanetza::asn1::Cam& CpObject::asn1() const
{
    return *m_cam_wrapper;
}


using namespace omnetpp;

class CpmStationIdResultFilter : public cObjectResultFilter
{
protected:
    void receiveSignal(cResultFilter* prev, simtime_t_cref t, cObject* object, cObject* details) override
    {
        if (auto cam = dynamic_cast<CpObject*>(object)) {
            const auto id = cam->asn1()->header.stationID;
            fire(this, t, id, details);
        }
    }
};

Register_ResultFilter("camStationId", CpmStationIdResultFilter)


class CpmGenerationDeltaTimeResultFilter : public cObjectResultFilter
{
protected:
    void receiveSignal(cResultFilter* prev, simtime_t_cref t, cObject* object, cObject* details) override
    {
        if (auto cam = dynamic_cast<CpObject*>(object)) {
            const auto genDeltaTime = cam->asn1()->cam.generationDeltaTime;
            fire(this, t, genDeltaTime, details);
        }
    }
};

Register_ResultFilter("camGenerationDeltaTime", CpmGenerationDeltaTimeResultFilter)

} // namespace artery
