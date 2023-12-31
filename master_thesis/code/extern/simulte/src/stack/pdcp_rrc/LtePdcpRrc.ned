//
//                           SimuLTE
//
// This file is part of a software released under the license included in file
// "license.pdf". This license can be also found at http://www.ltesimulator.com/
// The above file and the present reference are part of the software itself,
// and cannot be removed from it.
//


package lte.stack.pdcp_rrc;

//
// Interface for the PDCP/RRC layer of LTE Stack.
//
moduleinterface LtePdcpRrc {
    parameters:
        @display("i=block/fork");
        int headerCompressedSize @unit(B);
        bool ipBased;
        string nodeType;
    gates:
        input DataPortIpIn;
        input DataPortNonIpIn;
        output DataPortIpOut;
        output DataPortNonIpOut;
        inout EUTRAN_RRC_Sap;
        inout TM_Sap;
        inout UM_Sap;
        inout AM_Sap;
        inout control;
}


//
// Base module for the PDCP/RRC layer of LTE Stack.
//
simple LtePdcpRrcBase like LtePdcpRrc {
    parameters:
        @display("i=block/fork");
        int headerCompressedSize @unit(B) = default(-1B);    // Header compressed size (bytes) ( -1B = compression disabled
        int conversationalRlc @enum(TM, UM, AM, UNKNOWN_RLC_TYPE) = default(1);
        int streamingRlc @enum(TM, UM, AM, UNKNOWN_RLC_TYPE) = default(1);
        int interactiveRlc @enum(TM, UM, AM, UNKNOWN_RLC_TYPE) = default(1);
        int backgroundRlc @enum(TM, UM, AM, UNKNOWN_RLC_TYPE) = default(1);
        bool ipBased;
        string nodeType;
        //# Statistics
    
        gates:
        //#
        //# Gates connecting UE/eNB and PDCP/RRC Layer
        //#
        //# Data Ports
        
        input DataPortIpIn;
        input DataPortNonIpIn;
        output DataPortIpOut;
        output DataPortNonIpOut;
        
        //# Control Ports
        
        inout EUTRAN_RRC_Sap;    // Control of RRC Layer
        inout control;
        
        //#
        //# Gates connecting PDCP/RRC and RLC Layer
        //#
        //# Data Ports
        
        inout TM_Sap;            // Transparent Mode SAP
        inout UM_Sap;            // Unacknowledged Mode SAP
        inout AM_Sap;            // Acknowledged Mode SAP
        
        
}

//
// User Equipment PDCP/RRC layer of LTE stack
//
simple LtePdcpRrcUe extends LtePdcpRrcBase {
        @class("LtePdcpRrcUe");
}

//
// D2D-capable User Equipment PDCP/RRC layer of LTE stack
//
simple LtePdcpRrcUeD2D extends LtePdcpRrcUe {
    parameters:
        @class("LtePdcpRrcUeD2D");
}

//
// eNodeB PDCP/RRC layer of LTE stack
//
simple LtePdcpRrcEnb extends LtePdcpRrcBase {
        @class("LtePdcpRrcEnb");
}

//
// D2D-capable eNodeB PDCP/RRC layer of LTE stack
//
simple LtePdcpRrcEnbD2D extends LtePdcpRrcEnb {
        @class("LtePdcpRrcEnbD2D");
}

//
// Relay (UE side) PDCP/RRC layer of LTE stack
// Connection: eNodeB <--> Relay
//
simple LtePdcpRrcRelayUe extends LtePdcpRrcBase {
        @class("LtePdcpRrcRelayUe");
}

//
// Relay (eNB side) PDCP/RRC layer of LTE stack
// Connection: Relay <--> UE
//
simple LtePdcpRrcRelayEnb extends LtePdcpRrcBase {
        @class("LtePdcpRrcRelayEnb");
}
