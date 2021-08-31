PVObject_=pvModule
  Version=6.88
  Flags=$00900043

  PVObject_Commercial=pvCommercial
    Flags=$0041
    Manufacturer=Jinkosolar
    Model=JKM575M-7RL4-TV PRE01
    DataSource=Datasheet
    Width=1.134
    Height=2.411
    Depth=0.035
    Weight=30.930
    NPieces=100
    PriceDate=16/06/20 21:55
    Remarks, Count=8
      Str_1=AKTAR 29/06/2021
      Str_2
      Str_3=0.8% GAIN nameplate bias
      Str_4=0.1% LOSS Modelling error
      Str_5=1.5% LID as per guidance
      Str_6
      Str_7=1.8% std Isc
      Str_8=1.5% std Voc
    End of Remarks=1.5% std Voc
  End of PVObject pvCommercial

  Technol=mtSiMono
  NCelS=78
  NCelP=2
  NDiode=3
  SubModuleLayout=slTwinHalfCells
  GRef=1000
  TRef=25.0
  PNom=575.0
  PNomTolLow=0.00
  PNomTolUp=3.00
  BifacialityFactor=0.700
  Isc=13.690
  Voc=53.20
  Imp=12.870
  Vmp=44.68
  muISC=6.57
  muVocSpec=-148.9
  muPmpReq=-0.350
  RShunt=500
  Rp_0=2000
  Rp_Exp=5.50
  RSerie=0.203
  Gamma=1.009
  muGamma=-0.0004
  VMaxIEC=1500
  VMaxUL=1500
  Absorb=0.90
  ARev=3.200
  BRev=13.320
  RDiode=0.010
  VRevDiode=-0.70
  AirMassRef=1.500
  CellArea=147.6
  LIDLoss=1.50
  SandiaAMCorr=50.000
  RelEffic200=-3.50

  PVObject_IAM=pvIAM
    Flags=$00
    IAMMode=Ashrae
    B0_IAM=0.040
  End of PVObject pvIAM

  OperPoints, list of=1 tOperPoint
    Point_1=False,200,25.0,-3.50,0.00,0.000,0.000,0.00
  End of List OperPoints
End of PVObject pvModule
