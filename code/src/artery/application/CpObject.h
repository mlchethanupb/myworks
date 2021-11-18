#ifndef ARTERY_CPOBJECT_H_
#define ARTERY_CPOBJECT_H_

#include <omnetpp/cobject.h>
#include <vanetza/asn1/cam.hpp>
#include <memory>

namespace artery
{

class CpObject : public omnetpp::cObject
{
public:
    CpObject(const CpObject&) = default;
    CpObject& operator=(const CpObject&) = default;

    CpObject(vanetza::asn1::Cam&&);
    CpObject& operator=(vanetza::asn1::Cam&&);

    CpObject(const vanetza::asn1::Cam&);
    CpObject& operator=(const vanetza::asn1::Cam&);

    CpObject(const std::shared_ptr<const vanetza::asn1::Cam>&);
    CpObject& operator=(const std::shared_ptr<const vanetza::asn1::Cam>&);

    const vanetza::asn1::Cam& asn1() const;

    std::shared_ptr<const vanetza::asn1::Cam> shared_ptr() const;

private:
    std::shared_ptr<const vanetza::asn1::Cam> m_cam_wrapper;
};

} // namespace artery

#endif /* ARTERY_CPOBJECT_H_ */
