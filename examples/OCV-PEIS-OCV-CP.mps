EC-LAB SETTING FILE

Number of linked techniques : 4

EC-LAB for windows v11.61 (software)
Internet server v11.61 (firmware)
Command interpretor v11.61 (firmware)

Filename : G:\Active Group Members\Thorben\Code\biologic-com\examples\OCV-PEIS-OCV-CP.mps

Device : SP-150
CE vs. WE compliance from -10 V to 10 V
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -10.00 V, max = 10.00 V
Safety Limits :
	Do not start on E overload
Electrode material : 
Initial state : 
Electrolyte : 
Comments : 
Electrode surface area : 10.000 cm²
Characteristic mass : 1.000 mg
Equivalent Weight : 0.000 g/eq.
Density : 0.000 g/cm3
Volume (V) : 1.000 L
Cycle Definition : Charge/Discharge alternance
Turn to OCV between techniques

Technique : 1
Open Circuit Voltage
tR (h:m:s)          00:00:10.0000       
dER/dt (mV/h)       0.000               
record              Ewe                 
dER (mV)            0.000               
dtR (s)             1.000               
E range min (V)     -10.000             
E range max (V)     10.000              

Technique : 2
Potentio Electrochemical Impedance Spectroscopy
Mode                Single sine         
E (V)               0.000               
vs.                 Eoc                 
tE (h:m:s)          00:00:00.0000       
record              0                   
dI                  0.000               
unit dI             A                   
dt (s)              1.000               
fi                  1.000               
unit fi             MHz                 
ff                  1.000               
unit ff             Hz                  
Nd                  10                  
Points              per decade          
spacing             Logarithmic         
Va (mV)             10.000              
pw                  0.100               
Na                  2                   
corr                0                   
E range min (V)     -10                 
E range max (V)     10                  
I Range             Auto                
Bandwidth           7                   
nc cycles           0                   
goto Ns'            0                   
nr cycles           0                   
inc. cycle          0                   

Technique : 3
Open Circuit Voltage
tR (h:m:s)          00:00:10.0000       
dER/dt (mV/h)       0.000               
record              Ewe                 
dER (mV)            0.000               
dtR (s)             1.000               
E range min (V)     -10.000             
E range max (V)     10.000              

Technique : 4
Chronopotentiometry
Ns                  0                   1                   2                   3                   
Is                  0.000               1.000               -1.000              0.000               
unit Is             A                   µA                  µA                  A                   
vs.                 <None>              <None>              <None>              <None>              
ts (h:m:s)          00:00:10.0000       00:00:10.0000       00:00:10.0000       00:00:10.0000       
EM (V)              pass                pass                pass                pass                
dQM                 0.000               0.000               0.000               0.000               
unit dQM            A.h                 A.h                 A.h                 A.h                 
record              Ewe                 Ewe                 Ewe                 Ewe                 
dEs (mV)            0.000               0.000               0.000               0.000               
dts (s)             0.010               0.010               0.010               0.010               
E range min (V)     -10.000             -10.000             -10.000             -10.000             
E range max (V)     10.000              10.000              10.000              10.000              
I Range             10 µA               10 µA               10 µA               10 µA               
Bandwidth           7                   7                   7                   7                   
goto Ns'            0                   0                   0                   0                   
nc cycles           0                   0                   0                   0                   