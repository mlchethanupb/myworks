#include "artery/networking/AccessInterface.h"
#include "artery/networking/GeoNetPacket.h"
#include "artery/networking/GeoNetRequest.h"
#include "artery/utility/PointerCheck.h"
#include <omnetpp/checkandcast.h>
#include <omnetpp/csimplemodule.h>
#include <omnetpp/simutil.h>

using vanetza::access::DataRequest;
using vanetza::ChunkPacket;

namespace artery
{

AccessInterface::AccessInterface(omnetpp::cGate* gate) :
    mGateOut(notNullPtr(gate)),
    mModuleOut(omnetpp::check_and_cast<omnetpp::cSimpleModule*>(mGateOut->getOwnerModule()))
{
}

void AccessInterface::request(const DataRequest& request, std::unique_ptr<ChunkPacket> payload)
{
   //std::cout << "MLC artery::AccessInterface::request()" << std::endl;

    // Enter_Method on steroids...
    omnetpp::cMethodCallContextSwitcher ctx(mModuleOut);
    ctx.methodCall("request");

    GeoNetPacket* gn = new GeoNetPacket("GeoNet packet");
    gn->setPayload(std::move(payload));
    if( gn->hasPayload()){
        std::cout << "AccessInterface::request -- payload is not empty" << std::endl;
        std::cout << "AccessInterface::request -- payload size " << gn->getBitLength()  << std::endl;
    }else{
        std::cout << "AccessInterface::request -- payload is empty" << std::endl;
    }
    gn->setControlInfo(new GeoNetRequest(request));

    // gn has been created in the context of mModuleOut, thus ownership is fine
    mModuleOut->send(gn, mGateOut); //MLC mGateOut is radioDriverData$o
}

} // namespace artery
