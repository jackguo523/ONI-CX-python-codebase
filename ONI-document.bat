:: download all useful ONI documents

if not exist "ONI-document" mkdir ONI-document
cd ONI-document
if not exist "general" mkdir general
cd general
curl -L "https://drive.google.com/uc?export=download&id=1h0pRC6afyoQKnnCM421Di1PDgS1mXjQ-" -o NimOS-Manual.pdf
curl -L "https://drive.google.com/uc?export=download&id=1myXZAX1eV_IedRdSDR-3XRsR9H31XgHo" -o NimOS-Unpacking.pdf
curl -L "https://drive.google.com/uc?export=download&id=1WO7bFiNpgRkjdc3n9vUkHXQqzgpkk1Gb" -o NimOS-IT-Requirement.pdf
curl -L "https://drive.google.com/uc?export=download&id=1LcmoXoGbUOw77c0jhXvzem03Wl1YjPYM" -o NimOS-Site-Preparation.pdf




cd ../
if not exist "service-desk" mkdir service-desk
cd service-desk
curl -L "https://drive.google.com/uc?export=download&id=1Dc8MrLhmt-ye_vCbjFxoKR0Xj880Moos" -o ONI-NimOS-Installation.pdf

if not exist "sample-preparation" mkdir sample-preparation
cd sample-preparation
curl -L "https://drive.google.com/uc?export=download&id=1tkJYb9YuendH8pK25CUWqbIMlfs8GYf1" -o ONI-Load-Sample.pdf
curl -L "https://drive.google.com/uc?export=download&id=1KqH5_xEWflZhxzT-dSG7KBx1Ll-VXZCm" -o ONI-Prepare-Bead-Slide.pdf
curl -L "https://drive.google.com/uc?export=download&id=1AulbP4O1_bsBDla92Jh259E6bmQ_Ace6" -o ONI-Prepare-Highlighter.pdf
curl -L "https://drive.google.com/uc?export=download&id=1sNtUKblyyZC0rn-BdtbGjQjHHS0hHNBs" -o ONI-Prepare-dSTORM-Sample.pdf
curl -L "https://drive.google.com/uc?export=download&id=18uzyGEVIvqEQ32AZ5gdv5FmpDOMXBkdh" -o ONI-Prepare-EV-Sample.pdf
curl -L "https://drive.google.com/uc?export=download&id=1QCS52M7L6rw6K0BiuTXH_yi2VfrxpiB9" -o ONI-Prepare-Tracking-Sample.pdf
curl -L "https://drive.google.com/uc?export=download&id=1fcdCA6bPCynAcB37XiGXDRcswFNEu8Ew" -o ONI-EV-Protocol.pdf
curl -L "https://drive.google.com/uc?export=download&id=1LcmoXoGbUOw77c0jhXvzem03Wl1YjPYM" -o NimOS-dSTORM-Fluorophores.pdf
curl -L "https://drive.google.com/uc?export=download&id=19rQn_gVHKWE3vXqhrHpaXeoDG4oHX1qx" -o NimOS-PALM-Fluorophores.pdf

cd ../
if not exist "image-acquisition" mkdir image-acquisition
cd image-acquisition
if not exist "NimOS-control" mkdir NimOS-control
cd NimOS-control
curl -L "https://drive.google.com/uc?export=download&id=1VVee3t_P9n9iqAF8-lUF-ZiWtss9S9-W" -o ONI-NimOS-Overview.pdf
curl -L "https://drive.google.com/uc?export=download&id=1x1sAZf2KGPWdpMjdiTf52aBRBLLU5WG8" -o ONI-NimOS-Tabs.pdf
curl -L "https://drive.google.com/uc?export=download&id=1QAKMtfPhcKNVvdJuXaIW-VG2lTMSq4SE" -o ONI-NimOS-Keyboard-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=1FZKYBgFOgjhP6yMrOwNJ6EpQzLYA643l" -o ONI-NimOS-User-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=10EtpkX5ASV49uhQY6Zgk1qKd76anfek5" -o ONI-NimOS-Laser-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=13AuqqO8vUKyVwyNAydFYhlVnrV1w5Wj5" -o ONI-NimOS-Stage-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=1JPFAHIV8I7jiUoT1oAP7kP32SW9vR6HZ" -o ONI-NimOS-Optical-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=13S_QFkfcJNhJst1IQG7zvco8iEqtyNun" -o ONI-NimOS-Temperature-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=14XxJYH8AdZMl0ebfSMkU1D6k-7PoY2cX" -o ONI-NimOS-Acquisition-Control.pdf
curl -L "https://drive.google.com/uc?export=download&id=1cd10vUQ3nyuaq5d_WwIH5Rsu7blFlG8q" -o ONI-NimOS-Display-Control.pdf

cd ../
if not exist "NimOS-calibration" mkdir NimOS-calibration
cd NimOS-calibration
curl -L "https://drive.google.com/uc?export=download&id=1R5tymKKpYDZ1JA4pkJjgGuBRZgm6hKCb" -o ONI-NimOS-Camera-Calibration.pdf
curl -L "https://drive.google.com/uc?export=download&id=1hDGYlY1DK-gzL8esGQskAnatyaW-vIpm" -o ONI-NimOS-Channel-Mapping-Calibration.pdf
curl -L "https://drive.google.com/uc?export=download&id=1gV03UHOh1XbqpUTa536swe2Cg9i_JGWd" -o ONI-NimOS-3D-Mapping-Calibration.pdf

cd ../
if not exist "NimOS-function" mkdir NimOS-function
cd NimOS-function
curl -L "https://drive.google.com/uc?export=download&id=1TfaEW2f96T9RL24w-w9KR5_dInPJNlad" -o ONI-NimOS-Function-Multiacquisition.pdf
curl -L "https://drive.google.com/uc?export=download&id=1s2I9g8eg1XZiaO8NC-zExIXNoUgnZsmI" -o ONI-NimOS-Function-Light-Program.pdf
curl -L "https://drive.google.com/uc?export=download&id=1IqWWPRItCMwdStB6ocPV_XzMTMxFrSG-" -o ONI-NimOS-Function-Position-List.pdf
curl -L "https://drive.google.com/uc?export=download&id=1JLH620UPfgghtGLRJwNuvRl2QobtYv2t" -o ONI-NimOS-Function-Zlock.pdf
curl -L "https://drive.google.com/uc?export=download&id=136MCWTLyRPycuES7lnlaqat4Hs83rvoj" -o ONI-NimOS-Function-TIRF.pdf
curl -L "https://drive.google.com/uc?export=download&id=1_OAbHOlR1L9ad-IaLe8EBqxA6ft0wYCn" -o ONI-NimOS-Function-Confocal.pdf
curl -L "https://drive.google.com/uc?export=download&id=1HC55qwSXQeWGRhtJfZXwK-H-NWIp7hQT" -o ONI-NimOS-Function-3D.pdf
curl -L "https://drive.google.com/uc?export=download&id=1yzJhRiQGlnk0bYBaaz2PPHlR5oNjzE48" -o ONI-NimOS-Function-ROI.pdf
curl -L "https://drive.google.com/uc?export=download&id=17DmPnUtKGabaYs8q-cGuC-easfGgCTdL" -o ONI-NimOS-Function-Overview-Scan.pdf
curl -L "https://drive.google.com/uc?export=download&id=12FCUxEYNzooGgy15KRLsl0OiT-8jjePM" -o ONI-NimOS-Function-PythONI.pdf
curl -L "https://drive.google.com/uc?export=download&id=178MkZc00UG4oh34hP-xfGPoDZ9NHorcP" -o ONI-NimOS-Function-Tracking.pdf
curl -L "https://drive.google.com/uc?export=download&id=161hzb2-yjAnIMNWFGWvNSCw3zGkIndcL" -o ONI-NimOS-Function-FRET.pdf

cd ../
if not exist "NimOS-IO" mkdir NimOS-IO
cd NimOS-IO
curl -L "https://drive.google.com/uc?export=download&id=11nwaE_BA0zbKtqdTEeJaHO4K-oxFU4CM" -o ONI-NimOS-Data-Import.pdf
curl -L "https://drive.google.com/uc?export=download&id=18oRwAThib1KZaSMr5Z1OfmgxUQeERNKU" -o ONI-NimOS-Data-Export.pdf
curl -L "https://drive.google.com/uc?export=download&id=1cZ54cmK-EYsRv-A1geVspH0zrRivULfE" -o ONI-NimOS-Data-Metadata.pdf
curl -L "https://drive.google.com/uc?export=download&id=1qJ9nfK6nd6ok8ZaOeN2GoomgtVwud-Cr" -o ONI-NimOS-Data-Interpretation.pdf

cd ../
cd ../
if not exist "data-analysis" mkdir data-analysis
cd data-analysis
curl -L "https://drive.google.com/uc?export=download&id=18ayzbCb7pX-nh6yysacKx0_12P2IK1nJ" -o ONI-NimOS-Analysis-Tools.pdf
curl -L "https://drive.google.com/uc?export=download&id=1M0VTqVaIx15Fdm_zj7b41KfDs1V75IDX" -o ONI-NimOS-Analysis-Localizations.pdf
curl -L "https://drive.google.com/uc?export=download&id=1mqOMjsaMQv6b4f_lZETc37w_M94Nns1K" -o ONI-NimOS-Analysis-Filters.pdf
curl -L "https://drive.google.com/uc?export=download&id=1owBImT_AG6fZqm1SiSaYiT9Gikk_vu6Y" -o ONI-NimOS-Analysis-Viewing-Options.pdf
curl -L "https://drive.google.com/uc?export=download&id=1rZjBuaHAaKZzAvJFU7mHsrxez0wNyoP1" -o ONI-NimOS-Analysis-Drift-Correction.pdf

cd ../
if not exist "additional-document" mkdir additional-document
cd additional-document
curl -L "https://drive.google.com/uc?export=download&id=1pW4Qtu_o4F5lgzOZfpGH0DF9-jItuo5h" -o ONI-Maintenance.pdf
curl -L "https://drive.google.com/uc?export=download&id=1IDUHfH8TWWibmXrYOLWxBY-0JyacY5e4" -o ONI-Safety.pdf
curl -L "https://drive.google.com/uc?export=download&id=1bVrZLODubFuuXoRABMkwbMiiQBhDr258" -o ONI-FAQ.pdf