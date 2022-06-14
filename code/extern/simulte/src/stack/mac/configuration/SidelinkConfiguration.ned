//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package lte.stack.mac.configuration;

//
// TODO auto-generated module
//
simple SidelinkConfiguration
{
    parameters:
        
        @class("SidelinkConfiguration");
        
        //# TODO: Change this to use xmldoc to fill in these params as it's more complex than this.
        xml txConfig;
        int resourceReservationInterval = 100; // in ms variable RRI allowed for 5G
        int minGrantStartTime = 0;  // Between 0-20 ms
        int maximumAllowedLatency = 100;
        int numSubchannels = 5; 
        int subchannelSize = 10;//Number of PRB per subchannel 10, 12, 15, 20, 25, 50, 75, or 100
        double probResourceKeep = default(0.4);        
        int minMCSPSSCH = default(1);
        int maxMCSPSSCH = default(28);
        int allowedRetxNumberPSSCH = default(0);           
        int numberSubcarriersperPRB = default(12);
        int numberSymbolsPerSlot=default(7);
        int bitsPerSymbolQPSK=default(2);
        int resourceReselectionCounter = default(5);
        bool usePreconfiguredTxParams = default(false);
        
        //Signals and statistics collection
        
        
        
}
