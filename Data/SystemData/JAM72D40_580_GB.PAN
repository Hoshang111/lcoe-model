PVObject_=pvModule
  Version=7.2.12
  Flags=$00900043

  PVObject_Commercial=pvCommercial
    Comment=Shanghai JA Solar Technology Co., Ltd.
    Flags=$0041
    Manufacturer=JA Solar
    Model=JAM72D40-580/GB
    DataSource=JA internal
    YearBeg=2021
    Width=1.134
    Height=2.278
    Depth=0.030
    Weight=31.800
    NPieces=100
    PriceDate=26/04/20 17:20
    Remarks, Count=6
      Str_1=Frame: Aluminum
      Str_2=Structure: 2.0 mm Heat strengthened AR-coated glass
      Str_3=Connections: POE/Heat strengthened glass with white
      Str_4=glaze, Jbox
      Str_5
      Str_6
    End of Remarks
  End of PVObject pvCommercial

  Technol=mtSiMono
  NCelS=72
  NCelP=2
  NDiode=3
  SubModuleLayout=slTwinHalfCells
  FrontSurface=fsARCoating
  GRef=1000
  TRef=25.0
  PNom=580.0
  PNomTolLow=0.00
  PNomTolUp=0.95
  BifacialityFactor=0.800
  Isc=14.380
  Voc=51.30
  Imp=13.480
  Vmp=43.03
  muISC=6.60
  muVocSpec=-113.1
  muPmpReq=-0.300
  RShunt=350
  Rp_0=1400
  Rp_Exp=5.50
  RSerie=0.213
  Gamma=1.004
  muGamma=-0.0002
  VMaxIEC=1500
  VMaxUL=1500
  Absorb=0.90
  ARev=3.200
  BRev=11.496
  RDiode=0.010
  VRevDiode=-0.70
  AirMassRef=1.500
  CellArea=165.2
  SandiaAMCorr=50.000
  RelEffic800=0.25
  RelEffic600=0.49
  RelEffic400=-0.09
  RelEffic200=-1.73

  PVObject_IAM=pvIAM
    Flags=$00
    IAMMode=UserProfile
    IAMProfile=TCubicProfile
      NPtsMax=9
      NPtsEff=9
      LastCompile=$B18D
      Mode=3
      Point_1=0.0,1.00000
      Point_2=40.0,1.00000
      Point_3=50.0,1.00000
      Point_4=60.0,1.00000
      Point_5=70.0,0.95800
      Point_6=75.0,0.91700
      Point_7=80.0,0.84700
      Point_8=85.0,0.71000
      Point_9=90.0,0.00000
    End of TCubicProfile
  End of PVObject pvIAM

  OperPoints, list of=13 tOperPoint
    Point_1=False,100,15.0,0.86,0.00,0.000,0.000,0.00
    Point_2=False,200,15.0,1.20,0.00,0.000,0.000,0.00
    Point_3=False,400,15.0,2.89,0.00,0.000,0.000,0.00
    Point_4=False,600,15.0,3.23,0.00,0.000,0.000,0.00
    Point_5=False,800,15.0,3.24,0.00,0.000,0.000,0.00
    Point_6=False,1000,15.0,2.86,0.00,0.000,0.000,0.00
    Point_7=False,100,25.0,-2.69,0.00,0.000,0.000,0.00
    Point_8=False,200,25.0,-1.73,0.00,0.000,0.000,0.00
    Point_9=False,400,25.0,-0.09,0.00,0.000,0.000,0.00
    Point_10=False,600,25.0,0.49,0.00,0.000,0.000,0.00
    Point_11=False,800,25.0,0.25,0.00,0.000,0.000,0.00
    Point_12=False,1000,25.0,0.00,0.00,0.000,0.000,0.00
    Point_13=False,1100,25.0,-0.26,0.00,0.000,0.000,0.00
  End of List OperPoints
End of PVObject pvModule
