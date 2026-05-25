ZGI ; Read Globals from ZWR format
 ;---------------------------------------------------------------------------
 ; Vendored from WorldVistA/VistA Scripts/ZGI.m (submodule pin b7aecb9), with
 ; one IRIS fix: CONFIG below now recognizes IRIS ($ZV["IRIS") and uses the
 ; Cache-compatible device config (spec docs/vista-iris-container-spec-v2.md
 ; §5.4 -- IRIS-only fork). Loaded via ^%RI as part of routines.ro, then used by
 ; 00_import.py:  D LIST^ZGI("/path/globals.lst")
 ;
 ; Original copyright 2011 The Open Source Electronic Health Record Agent,
 ; Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0).
 ;---------------------------------------------------------------------------
 N  D CONFIG
 W "ZWR Global Input",! X CONFIG("ASKIO") Q:IO=""  W !
 I '$$LOAD(IO) Q
 U $P W "Loaded "_IO,!
 Q
LOAD(IO) ; Read Globals from IO device in ZWR format
 N CONFIG D CONFIG
 N Q,S S Q=1
 C IO X CONFIG("OPENIO") I '$T W "Failed to open: "_IO,! Q 0
 I '($$READLINE(.H1)&$$READLINE(.H2)&(H2["ZWR")) U $P W "Not a ZWR: "_IO,! S Q=0 G QUIT
 F  Q:'$$READLINE(.S)  S @S
 G QUIT
LIST(IO,DIR) ; Read list from IO, load Globals from each DIR<entry> device
 N CONFIG D CONFIG
 N Q,ZWR S Q=1
 S DIR=$G(DIR,"")
 C IO X CONFIG("OPENIO") I '$T W "Failed to open: "_IO,! Q 0
 F  Q:'$$READLINE(.ZWR)  U $P W DIR_ZWR,! I '$$LOAD(DIR_ZWR) S Q=0
 G QUIT
 ;---------------------------------------------------------------------------
 ; Private implementation entry points below
 ;
READLINE(LINE)
 N $ES,$ET,EOF S EOF=0 X CONFIG("ETRAP")
 D READLN(.LINE)
 Q '($ZEOF!EOF)
READLN(LINE)
 S LINE=""
 U IO R LINE
 Q
ETRAP
 I @(CONFIG("ENDOFFILE")) S EOF=-1
 S $EC=""
 Q
QUIT
 C IO
 Q Q
CONFIG
 I $D(CONFIG) Q
 I ($ZV["Cache")!($ZV["IRIS") D  Q
 . S CONFIG("ASKIO")="D IN^%IS I POP S IO="""""
 . S CONFIG("OPENIO")="O IO:(""R""):0"
 . S CONFIG("ETRAP")="S $ET=""G ETRAP"""
 . S CONFIG("ENDOFFILE")="$ZE[""ENDOFFILE"""
 I $ZV["GT.M" D  Q
 . S CONFIG("ASKIO")="D ASKIO"
 . S CONFIG("OPENIO")="O IO:(readonly):0"
 . S CONFIG("ETRAP")="U IO:(exception=""G ETRAP"")"
 . S CONFIG("ENDOFFILE")="$ZS[""IOEOF"""
 W "ZGI does not support "_$ZV,!
 Q
ASKIO
 R "Device: ",IO,!
 I IO="" G ASKIO
 I IO="^" S IO=""
 Q
