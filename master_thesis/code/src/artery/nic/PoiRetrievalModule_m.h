//
// Generated file, do not edit! Created by nedtool 5.6 from /home/hegde/Workspace/PhD/v2xframework/artery/src/artery/nic/PoiRetrievalModule.msg.
//

#ifndef __ARTERY_POIRETRIEVALMODULE_M_H
#define __ARTERY_POIRETRIEVALMODULE_M_H

#if defined(__clang__)
#  pragma clang diagnostic ignored "-Wreserved-id-macro"
#endif
#include <omnetpp.h>

// nedtool version check
#define MSGC_VERSION 0x0507
#if (MSGC_VERSION!=OMNETPP_VERSION)
#    error Version mismatch! Probably this file was generated by an earlier version of nedtool: 'make clean' should help.
#endif


namespace artery {

/**
 * Class generated from <tt>/home/hegde/Workspace/PhD/v2xframework/artery/src/artery/nic/PoiRetrievalModule.msg:21</tt> by nedtool.
 * <pre>
 * //
 * // TODO generated message class
 * //
 * packet PoiRetrievalModule
 * {
 *     \@customize(true);
 * }
 * </pre>
 *
 * PoiRetrievalModule_Base is only useful if it gets subclassed, and PoiRetrievalModule is derived from it.
 * The minimum code to be written for PoiRetrievalModule is the following:
 *
 * <pre>
 * class PoiRetrievalModule : public PoiRetrievalModule_Base
 * {
 *   private:
 *     void copy(const PoiRetrievalModule& other) { ... }

 *   public:
 *     PoiRetrievalModule(const char *name=nullptr, short kind=0) : PoiRetrievalModule_Base(name,kind) {}
 *     PoiRetrievalModule(const PoiRetrievalModule& other) : PoiRetrievalModule_Base(other) {copy(other);}
 *     PoiRetrievalModule& operator=(const PoiRetrievalModule& other) {if (this==&other) return *this; PoiRetrievalModule_Base::operator=(other); copy(other); return *this;}
 *     virtual PoiRetrievalModule *dup() const override {return new PoiRetrievalModule(*this);}
 *     // ADD CODE HERE to redefine and implement pure virtual functions from PoiRetrievalModule_Base
 * };
 * </pre>
 *
 * The following should go into a .cc (.cpp) file:
 *
 * <pre>
 * Register_Class(PoiRetrievalModule)
 * </pre>
 */
class PoiRetrievalModule_Base : public ::omnetpp::cPacket
{
  protected:

  private:
    void copy(const PoiRetrievalModule_Base& other);

  protected:
    // protected and unimplemented operator==(), to prevent accidental usage
    bool operator==(const PoiRetrievalModule_Base&);
    // make constructors protected to avoid instantiation
    PoiRetrievalModule_Base(const char *name=nullptr, short kind=0);
    PoiRetrievalModule_Base(const PoiRetrievalModule_Base& other);
    // make assignment operator protected to force the user override it
    PoiRetrievalModule_Base& operator=(const PoiRetrievalModule_Base& other);

  public:
    virtual ~PoiRetrievalModule_Base();
    virtual PoiRetrievalModule_Base *dup() const override {throw omnetpp::cRuntimeError("You forgot to manually add a dup() function to class PoiRetrievalModule");}
    virtual void parsimPack(omnetpp::cCommBuffer *b) const override;
    virtual void parsimUnpack(omnetpp::cCommBuffer *b) override;

    // field getter/setter methods
};

} // namespace artery

#endif // ifndef __ARTERY_POIRETRIEVALMODULE_M_H

