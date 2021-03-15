# The System Class

A System class has been provided to feed data to the Plugin class at the discretion of the
Plugin's developer.
System information can be obtained using the following syntax:

    ```
    system = System()
    system_info = system.info()
    ```

In this above example, the system_info variable will be filled with a dictionary of a range
of system information.

An example of the available data:

```
{
    "devices": {
        "cpu_info": {
            "cpuinfo_version": [
                7,
                0,
                0
            ],
            "cpuinfo_version_string": "7.0.0",
            "arch": "X86_64",
            "bits": 64,
            "count": 8,
            "arch_string_raw": "x86_64",
            "vendor_id_raw": "GenuineIntel",
            "brand_raw": "Intel(R) Core(TM) i7-6770HQ CPU @ 2.60GHz",
            "hz_advertised_friendly": "2.6000 GHz",
            "hz_actual_friendly": "2.8001 GHz",
            "hz_advertised": [
                2600000000,
                0
            ],
            "hz_actual": [
                2800121000,
                0
            ],
            "stepping": 3,
            "model": 94,
            "family": 6,
            "flags": [
                "3dnowprefetch",
                "abm",
                "acpi",
                "adx",
                "aes",
                "aperfmperf",
                "apic",
                "arat",
                "arch_perfmon",
                "art",
                "avx",
                "avx2",
                "bmi1",
                "bmi2",
                "bts",
                "clflush",
                "clflushopt",
                "cmov",
                "constant_tsc",
                "cpuid",
                "cpuid_fault",
                "cx16",
                "cx8",
                "de",
                "ds_cpl",
                "dtes64",
                "dtherm",
                "dts",
                "epb",
                "ept",
                "ept_ad",
                "erms",
                "est",
                "f16c",
                "flexpriority",
                "flush_l1d",
                "fma",
                "fpu",
                "fsgsbase",
                "fxsr",
                "hle",
                "ht",
                "hwp",
                "hwp_act_window",
                "hwp_epp",
                "hwp_notify",
                "ibpb",
                "ibrs",
                "ida",
                "intel_pt",
                "invpcid",
                "invpcid_single",
                "lahf_lm",
                "lm",
                "mca",
                "mce",
                "md_clear",
                "mmx",
                "monitor",
                "movbe",
                "mpx",
                "msr",
                "mtrr",
                "nonstop_tsc",
                "nopl",
                "nx",
                "osxsave",
                "pae",
                "pat",
                "pbe",
                "pcid",
                "pclmulqdq",
                "pdcm",
                "pdpe1gb",
                "pebs",
                "pge",
                "pln",
                "pni",
                "popcnt",
                "pse",
                "pse36",
                "pti",
                "pts",
                "rdrand",
                "rdrnd",
                "rdseed",
                "rdtscp",
                "rep_good",
                "rtm",
                "sdbg",
                "sep",
                "sgx",
                "smap",
                "smep",
                "ss",
                "ssbd",
                "sse",
                "sse2",
                "sse4_1",
                "sse4_2",
                "ssse3",
                "stibp",
                "syscall",
                "tm",
                "tm2",
                "tpr_shadow",
                "tsc",
                "tsc_adjust",
                "tsc_deadline_timer",
                "tscdeadline",
                "vme",
                "vmx",
                "vnmi",
                "vpid",
                "x2apic",
                "xgetbv1",
                "xsave",
                "xsavec",
                "xsaveopt",
                "xsaves",
                "xtopology",
                "xtpr"
            ],
            "l3_cache_size": 6291456,
            "l2_cache_size": "1 MiB",
            "l1_data_cache_size": "128 KiB",
            "l1_instruction_cache_size": "128 KiB",
            "l2_cache_line_size": 256,
            "l2_cache_associativity": 6
        },
        "gpu_info": []
    },
    "ffmpeg": {
        "versions": {
            "program_version": {
                "version": "4.3.1-static https://johnvansickle.com/ffmpeg/ ",
                "copyright": "Copyright (c) 2007-2020 the FFmpeg developers",
                "compiler_ident": "gcc 8 (Debian 8.3.0-6)",
                "configuration": "--enable-gpl --enable-version3 --enable-static --disable-debug --disable-ffplay --disable-indev=sndio --disable-outdev=sndio --cc=gcc --enable-fontconfig --enable-frei0r --enable-gnutls --enable-gmp --enable-libgme --enable-gray --enable-libaom --enable-libfribidi --enable-libass --enable-libvmaf --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-librubberband --enable-libsoxr --enable-libspeex --enable-libsrt --enable-libvorbis --enable-libopus --enable-libtheora --enable-libvidstab --enable-libvo-amrwbenc --enable-libvpx --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libdav1d --enable-libxvid --enable-libzvbi --enable-libzimg"
            },
            "library_versions": [
                {
                    "name": "libavutil",
                    "major": 56,
                    "minor": 51,
                    "micro": 100,
                    "version": 3683172,
                    "ident": "Lavu56.51.100"
                },
                {
                    "name": "libavcodec",
                    "major": 58,
                    "minor": 91,
                    "micro": 100,
                    "version": 3824484,
                    "ident": "Lavc58.91.100"
                },
                {
                    "name": "libavformat",
                    "major": 58,
                    "minor": 45,
                    "micro": 100,
                    "version": 3812708,
                    "ident": "Lavf58.45.100"
                },
                {
                    "name": "libavdevice",
                    "major": 58,
                    "minor": 10,
                    "micro": 100,
                    "version": 3803748,
                    "ident": "Lavd58.10.100"
                },
                {
                    "name": "libavfilter",
                    "major": 7,
                    "minor": 85,
                    "micro": 100,
                    "version": 480612,
                    "ident": "Lavfi7.85.100"
                },
                {
                    "name": "libswscale",
                    "major": 5,
                    "minor": 7,
                    "micro": 100,
                    "version": 329572,
                    "ident": "SwS5.7.100"
                },
                {
                    "name": "libswresample",
                    "major": 3,
                    "minor": 7,
                    "micro": 100,
                    "version": 198500,
                    "ident": "SwR3.7.100"
                },
                {
                    "name": "libpostproc",
                    "major": 55,
                    "minor": 7,
                    "micro": 100,
                    "version": 3606372,
                    "ident": "postproc55.7.100"
                }
            ]
        },
        "hw_acceleration_methods": [
            "vdpau"
        ],
        "decoders": {
            "audio": {
                "8svx_exp": {
                    "capabilities": "A....D",
                    "description": "8SVX exponential"
                },
                "8svx_fib": {
                    "capabilities": "A....D",
                    "description": "8SVX fibonacci"
                },
                "aac": {
                    "capabilities": "A....D",
                    "description": "AAC (Advanced Audio Coding)"
                },
                "aac_fixed": {
                    "capabilities": "A....D",
                    "description": "AAC (Advanced Audio Coding) (codec aac)"
                },
                "aac_latm": {
                    "capabilities": "A....D",
                    "description": "AAC LATM (Advanced Audio Coding LATM syntax)"
                },
                "ac3": {
                    "capabilities": "A....D",
                    "description": "ATSC A/52A (AC-3)"
                },
                "ac3_fixed": {
                    "capabilities": "A....D",
                    "description": "ATSC A/52A (AC-3) (codec ac3)"
                },
                "acelp.kelvin": {
                    "capabilities": "A....D",
                    "description": "Sipro ACELP.KELVIN"
                },
                "adpcm_4xm": {
                    "capabilities": "A....D",
                    "description": "ADPCM 4X Movie"
                },
                "adpcm_adx": {
                    "capabilities": "A....D",
                    "description": "SEGA CRI ADX ADPCM"
                },
                "adpcm_afc": {
                    "capabilities": "A....D",
                    "description": "ADPCM Nintendo Gamecube AFC"
                },
                "adpcm_agm": {
                    "capabilities": "A....D",
                    "description": "ADPCM AmuseGraphics Movie"
                },
                "adpcm_aica": {
                    "capabilities": "A....D",
                    "description": "ADPCM Yamaha AICA"
                },
                "adpcm_argo": {
                    "capabilities": "A....D",
                    "description": "ADPCM Argonaut Games"
                },
                "adpcm_ct": {
                    "capabilities": "A....D",
                    "description": "ADPCM Creative Technology"
                },
                "adpcm_dtk": {
                    "capabilities": "A....D",
                    "description": "ADPCM Nintendo Gamecube DTK"
                },
                "adpcm_ea": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts"
                },
                "adpcm_ea_maxis_xa": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts Maxis CDROM XA"
                },
                "adpcm_ea_r1": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts R1"
                },
                "adpcm_ea_r2": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts R2"
                },
                "adpcm_ea_r3": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts R3"
                },
                "adpcm_ea_xas": {
                    "capabilities": "A....D",
                    "description": "ADPCM Electronic Arts XAS"
                },
                "g722": {
                    "capabilities": "A....D",
                    "description": "G.722 ADPCM (codec adpcm_g722)"
                },
                "g726": {
                    "capabilities": "A....D",
                    "description": "G.726 ADPCM (codec adpcm_g726)"
                },
                "g726le": {
                    "capabilities": "A....D",
                    "description": "G.726 ADPCM little-endian (codec adpcm_g726le)"
                },
                "adpcm_ima_alp": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA High Voltage Software ALP"
                },
                "adpcm_ima_amv": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA AMV"
                },
                "adpcm_ima_apc": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA CRYO APC"
                },
                "adpcm_ima_apm": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Ubisoft APM"
                },
                "adpcm_ima_cunning": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Cunning Developments"
                },
                "adpcm_ima_dat4": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Eurocom DAT4"
                },
                "adpcm_ima_dk3": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Duck DK3"
                },
                "adpcm_ima_dk4": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Duck DK4"
                },
                "adpcm_ima_ea_eacs": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Electronic Arts EACS"
                },
                "adpcm_ima_ea_sead": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Electronic Arts SEAD"
                },
                "adpcm_ima_iss": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Funcom ISS"
                },
                "adpcm_ima_mtf": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Capcom's MT Framework"
                },
                "adpcm_ima_oki": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Dialogic OKI"
                },
                "adpcm_ima_qt": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA QuickTime"
                },
                "adpcm_ima_rad": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Radical"
                },
                "adpcm_ima_smjpeg": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Loki SDL MJPEG"
                },
                "adpcm_ima_ssi": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Simon & Schuster Interactive"
                },
                "adpcm_ima_wav": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA WAV"
                },
                "adpcm_ima_ws": {
                    "capabilities": "A....D",
                    "description": "ADPCM IMA Westwood"
                },
                "adpcm_ms": {
                    "capabilities": "A....D",
                    "description": "ADPCM Microsoft"
                },
                "adpcm_mtaf": {
                    "capabilities": "A....D",
                    "description": "ADPCM MTAF"
                },
                "adpcm_psx": {
                    "capabilities": "A....D",
                    "description": "ADPCM Playstation"
                },
                "adpcm_sbpro_2": {
                    "capabilities": "A....D",
                    "description": "ADPCM Sound Blaster Pro 2-bit"
                },
                "adpcm_sbpro_3": {
                    "capabilities": "A....D",
                    "description": "ADPCM Sound Blaster Pro 2.6-bit"
                },
                "adpcm_sbpro_4": {
                    "capabilities": "A....D",
                    "description": "ADPCM Sound Blaster Pro 4-bit"
                },
                "adpcm_swf": {
                    "capabilities": "A....D",
                    "description": "ADPCM Shockwave Flash"
                },
                "adpcm_thp": {
                    "capabilities": "A....D",
                    "description": "ADPCM Nintendo THP"
                },
                "adpcm_thp_le": {
                    "capabilities": "A....D",
                    "description": "ADPCM Nintendo THP (little-endian)"
                },
                "adpcm_vima": {
                    "capabilities": "A....D",
                    "description": "LucasArts VIMA audio"
                },
                "adpcm_xa": {
                    "capabilities": "A....D",
                    "description": "ADPCM CDROM XA"
                },
                "adpcm_yamaha": {
                    "capabilities": "A....D",
                    "description": "ADPCM Yamaha"
                },
                "adpcm_zork": {
                    "capabilities": "A....D",
                    "description": "ADPCM Zork"
                },
                "alac": {
                    "capabilities": "AF...D",
                    "description": "ALAC (Apple Lossless Audio Codec)"
                },
                "amrnb": {
                    "capabilities": "A....D",
                    "description": "AMR-NB (Adaptive Multi-Rate NarrowBand) (codec amr_nb)"
                },
                "libopencore_amrnb": {
                    "capabilities": "A....D",
                    "description": "OpenCORE AMR-NB (Adaptive Multi-Rate Narrow-Band) (codec amr_nb)"
                },
                "amrwb": {
                    "capabilities": "A....D",
                    "description": "AMR-WB (Adaptive Multi-Rate WideBand) (codec amr_wb)"
                },
                "libopencore_amrwb": {
                    "capabilities": "A....D",
                    "description": "OpenCORE AMR-WB (Adaptive Multi-Rate Wide-Band) (codec amr_wb)"
                },
                "ape": {
                    "capabilities": "A....D",
                    "description": "Monkey's Audio"
                },
                "aptx": {
                    "capabilities": "A....D",
                    "description": "aptX (Audio Processing Technology for Bluetooth)"
                },
                "aptx_hd": {
                    "capabilities": "A....D",
                    "description": "aptX HD (Audio Processing Technology for Bluetooth)"
                },
                "atrac1": {
                    "capabilities": "A....D",
                    "description": "ATRAC1 (Adaptive TRansform Acoustic Coding)"
                },
                "atrac3": {
                    "capabilities": "A....D",
                    "description": "ATRAC3 (Adaptive TRansform Acoustic Coding 3)"
                },
                "atrac3al": {
                    "capabilities": "A....D",
                    "description": "ATRAC3 AL (Adaptive TRansform Acoustic Coding 3 Advanced Lossless)"
                },
                "atrac3plus": {
                    "capabilities": "A....D",
                    "description": "ATRAC3+ (Adaptive TRansform Acoustic Coding 3+) (codec atrac3p)"
                },
                "atrac3plusal": {
                    "capabilities": "A....D",
                    "description": "ATRAC3+ AL (Adaptive TRansform Acoustic Coding 3+ Advanced Lossless) (codec atrac3pal)"
                },
                "atrac9": {
                    "capabilities": "A....D",
                    "description": "ATRAC9 (Adaptive TRansform Acoustic Coding 9)"
                },
                "on2avc": {
                    "capabilities": "A....D",
                    "description": "On2 Audio for Video Codec (codec avc)"
                },
                "binkaudio_dct": {
                    "capabilities": "A....D",
                    "description": "Bink Audio (DCT)"
                },
                "binkaudio_rdft": {
                    "capabilities": "A....D",
                    "description": "Bink Audio (RDFT)"
                },
                "bmv_audio": {
                    "capabilities": "A....D",
                    "description": "Discworld II BMV audio"
                },
                "comfortnoise": {
                    "capabilities": "A....D",
                    "description": "RFC 3389 comfort noise generator"
                },
                "cook": {
                    "capabilities": "A....D",
                    "description": "Cook / Cooker / Gecko (RealAudio G2)"
                },
                "derf_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Xilam DERF"
                },
                "dolby_e": {
                    "capabilities": "A....D",
                    "description": "Dolby E"
                },
                "dsd_lsbf": {
                    "capabilities": "A.S..D",
                    "description": "DSD (Direct Stream Digital), least significant bit first"
                },
                "dsd_lsbf_planar": {
                    "capabilities": "A.S..D",
                    "description": "DSD (Direct Stream Digital), least significant bit first, planar"
                },
                "dsd_msbf": {
                    "capabilities": "A.S..D",
                    "description": "DSD (Direct Stream Digital), most significant bit first"
                },
                "dsd_msbf_planar": {
                    "capabilities": "A.S..D",
                    "description": "DSD (Direct Stream Digital), most significant bit first, planar"
                },
                "dsicinaudio": {
                    "capabilities": "A....D",
                    "description": "Delphine Software International CIN audio"
                },
                "dss_sp": {
                    "capabilities": "A....D",
                    "description": "Digital Speech Standard - Standard Play mode (DSS SP)"
                },
                "dst": {
                    "capabilities": "A....D",
                    "description": "DST (Digital Stream Transfer)"
                },
                "dca": {
                    "capabilities": "A....D",
                    "description": "DCA (DTS Coherent Acoustics) (codec dts)"
                },
                "dvaudio": {
                    "capabilities": "A....D",
                    "description": "Ulead DV Audio"
                },
                "eac3": {
                    "capabilities": "A....D",
                    "description": "ATSC A/52B (AC-3, E-AC-3)"
                },
                "evrc": {
                    "capabilities": "A....D",
                    "description": "EVRC (Enhanced Variable Rate Codec)"
                },
                "flac": {
                    "capabilities": "AF...D",
                    "description": "FLAC (Free Lossless Audio Codec)"
                },
                "g723_1": {
                    "capabilities": "A....D",
                    "description": "G.723.1"
                },
                "g729": {
                    "capabilities": "A....D",
                    "description": "G.729"
                },
                "gremlin_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Gremlin"
                },
                "gsm": {
                    "capabilities": "A....D",
                    "description": "GSM"
                },
                "gsm_ms": {
                    "capabilities": "A....D",
                    "description": "GSM Microsoft variant"
                },
                "hca": {
                    "capabilities": "A....D",
                    "description": "CRI HCA"
                },
                "hcom": {
                    "capabilities": "A....D",
                    "description": "HCOM Audio"
                },
                "iac": {
                    "capabilities": "A....D",
                    "description": "IAC (Indeo Audio Coder)"
                },
                "ilbc": {
                    "capabilities": "A....D",
                    "description": "iLBC (Internet Low Bitrate Codec)"
                },
                "imc": {
                    "capabilities": "A....D",
                    "description": "IMC (Intel Music Coder)"
                },
                "interplay_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Interplay"
                },
                "interplayacm": {
                    "capabilities": "A....D",
                    "description": "Interplay ACM"
                },
                "mace3": {
                    "capabilities": "A....D",
                    "description": "MACE (Macintosh Audio Compression/Expansion) 3:1"
                },
                "mace6": {
                    "capabilities": "A....D",
                    "description": "MACE (Macintosh Audio Compression/Expansion) 6:1"
                },
                "metasound": {
                    "capabilities": "A....D",
                    "description": "Voxware MetaSound"
                },
                "mlp": {
                    "capabilities": "A....D",
                    "description": "MLP (Meridian Lossless Packing)"
                },
                "mp1": {
                    "capabilities": "A....D",
                    "description": "MP1 (MPEG audio layer 1)"
                },
                "mp1float": {
                    "capabilities": "A....D",
                    "description": "MP1 (MPEG audio layer 1) (codec mp1)"
                },
                "mp2": {
                    "capabilities": "A....D",
                    "description": "MP2 (MPEG audio layer 2)"
                },
                "mp2float": {
                    "capabilities": "A....D",
                    "description": "MP2 (MPEG audio layer 2) (codec mp2)"
                },
                "mp3float": {
                    "capabilities": "A....D",
                    "description": "MP3 (MPEG audio layer 3) (codec mp3)"
                },
                "mp3": {
                    "capabilities": "A....D",
                    "description": "MP3 (MPEG audio layer 3)"
                },
                "mp3adufloat": {
                    "capabilities": "A....D",
                    "description": "ADU (Application Data Unit) MP3 (MPEG audio layer 3) (codec mp3adu)"
                },
                "mp3adu": {
                    "capabilities": "A....D",
                    "description": "ADU (Application Data Unit) MP3 (MPEG audio layer 3)"
                },
                "mp3on4float": {
                    "capabilities": "A....D",
                    "description": "MP3onMP4 (codec mp3on4)"
                },
                "mp3on4": {
                    "capabilities": "A....D",
                    "description": "MP3onMP4"
                },
                "als": {
                    "capabilities": "A....D",
                    "description": "MPEG-4 Audio Lossless Coding (ALS) (codec mp4als)"
                },
                "mpc7": {
                    "capabilities": "A....D",
                    "description": "Musepack SV7 (codec musepack7)"
                },
                "mpc8": {
                    "capabilities": "A....D",
                    "description": "Musepack SV8 (codec musepack8)"
                },
                "nellymoser": {
                    "capabilities": "A....D",
                    "description": "Nellymoser Asao"
                },
                "opus": {
                    "capabilities": "A....D",
                    "description": "Opus"
                },
                "libopus": {
                    "capabilities": "A....D",
                    "description": "libopus Opus (codec opus)"
                },
                "paf_audio": {
                    "capabilities": "A....D",
                    "description": "Amazing Studio Packed Animation File Audio"
                },
                "pcm_alaw": {
                    "capabilities": "A....D",
                    "description": "PCM A-law / G.711 A-law"
                },
                "pcm_bluray": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16|20|24-bit big-endian for Blu-ray media"
                },
                "pcm_dvd": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16|20|24-bit big-endian for DVD media"
                },
                "pcm_f16le": {
                    "capabilities": "A....D",
                    "description": "PCM 16.8 floating point little-endian"
                },
                "pcm_f24le": {
                    "capabilities": "A....D",
                    "description": "PCM 24.0 floating point little-endian"
                },
                "pcm_f32be": {
                    "capabilities": "A....D",
                    "description": "PCM 32-bit floating point big-endian"
                },
                "pcm_f32le": {
                    "capabilities": "A....D",
                    "description": "PCM 32-bit floating point little-endian"
                },
                "pcm_f64be": {
                    "capabilities": "A....D",
                    "description": "PCM 64-bit floating point big-endian"
                },
                "pcm_f64le": {
                    "capabilities": "A....D",
                    "description": "PCM 64-bit floating point little-endian"
                },
                "pcm_lxf": {
                    "capabilities": "A....D",
                    "description": "PCM signed 20-bit little-endian planar"
                },
                "pcm_mulaw": {
                    "capabilities": "A....D",
                    "description": "PCM mu-law / G.711 mu-law"
                },
                "pcm_s16be": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16-bit big-endian"
                },
                "pcm_s16be_planar": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16-bit big-endian planar"
                },
                "pcm_s16le": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16-bit little-endian"
                },
                "pcm_s16le_planar": {
                    "capabilities": "A....D",
                    "description": "PCM signed 16-bit little-endian planar"
                },
                "pcm_s24be": {
                    "capabilities": "A....D",
                    "description": "PCM signed 24-bit big-endian"
                },
                "pcm_s24daud": {
                    "capabilities": "A....D",
                    "description": "PCM D-Cinema audio signed 24-bit"
                },
                "pcm_s24le": {
                    "capabilities": "A....D",
                    "description": "PCM signed 24-bit little-endian"
                },
                "pcm_s24le_planar": {
                    "capabilities": "A....D",
                    "description": "PCM signed 24-bit little-endian planar"
                },
                "pcm_s32be": {
                    "capabilities": "A....D",
                    "description": "PCM signed 32-bit big-endian"
                },
                "pcm_s32le": {
                    "capabilities": "A....D",
                    "description": "PCM signed 32-bit little-endian"
                },
                "pcm_s32le_planar": {
                    "capabilities": "A....D",
                    "description": "PCM signed 32-bit little-endian planar"
                },
                "pcm_s64be": {
                    "capabilities": "A....D",
                    "description": "PCM signed 64-bit big-endian"
                },
                "pcm_s64le": {
                    "capabilities": "A....D",
                    "description": "PCM signed 64-bit little-endian"
                },
                "pcm_s8": {
                    "capabilities": "A....D",
                    "description": "PCM signed 8-bit"
                },
                "pcm_s8_planar": {
                    "capabilities": "A....D",
                    "description": "PCM signed 8-bit planar"
                },
                "pcm_u16be": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 16-bit big-endian"
                },
                "pcm_u16le": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 16-bit little-endian"
                },
                "pcm_u24be": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 24-bit big-endian"
                },
                "pcm_u24le": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 24-bit little-endian"
                },
                "pcm_u32be": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 32-bit big-endian"
                },
                "pcm_u32le": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 32-bit little-endian"
                },
                "pcm_u8": {
                    "capabilities": "A....D",
                    "description": "PCM unsigned 8-bit"
                },
                "pcm_vidc": {
                    "capabilities": "A....D",
                    "description": "PCM Archimedes VIDC"
                },
                "qcelp": {
                    "capabilities": "A....D",
                    "description": "QCELP / PureVoice"
                },
                "qdm2": {
                    "capabilities": "A....D",
                    "description": "QDesign Music Codec 2"
                },
                "qdmc": {
                    "capabilities": "A....D",
                    "description": "QDesign Music Codec 1"
                },
                "real_144": {
                    "capabilities": "A....D",
                    "description": "RealAudio 1.0 (14.4K) (codec ra_144)"
                },
                "real_288": {
                    "capabilities": "A....D",
                    "description": "RealAudio 2.0 (28.8K) (codec ra_288)"
                },
                "ralf": {
                    "capabilities": "A....D",
                    "description": "RealAudio Lossless"
                },
                "roq_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM id RoQ"
                },
                "s302m": {
                    "capabilities": "A....D",
                    "description": "SMPTE 302M"
                },
                "sbc": {
                    "capabilities": "A....D",
                    "description": "SBC (low-complexity subband codec)"
                },
                "sdx2_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Squareroot-Delta-Exact"
                },
                "shorten": {
                    "capabilities": "A....D",
                    "description": "Shorten"
                },
                "sipr": {
                    "capabilities": "A....D",
                    "description": "RealAudio SIPR / ACELP.NET"
                },
                "siren": {
                    "capabilities": "A....D",
                    "description": "Siren"
                },
                "smackaud": {
                    "capabilities": "A....D",
                    "description": "Smacker audio (codec smackaudio)"
                },
                "sol_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Sol"
                },
                "sonic": {
                    "capabilities": "A..X.D",
                    "description": "Sonic"
                },
                "libspeex": {
                    "capabilities": "A....D",
                    "description": "libspeex Speex (codec speex)"
                },
                "tak": {
                    "capabilities": "AF...D",
                    "description": "TAK (Tom's lossless Audio Kompressor)"
                },
                "truehd": {
                    "capabilities": "A....D",
                    "description": "TrueHD"
                },
                "truespeech": {
                    "capabilities": "A....D",
                    "description": "DSP Group TrueSpeech"
                },
                "tta": {
                    "capabilities": "AF...D",
                    "description": "TTA (True Audio)"
                },
                "twinvq": {
                    "capabilities": "A....D",
                    "description": "VQF TwinVQ"
                },
                "vmdaudio": {
                    "capabilities": "A....D",
                    "description": "Sierra VMD audio"
                },
                "vorbis": {
                    "capabilities": "A....D",
                    "description": "Vorbis"
                },
                "libvorbis": {
                    "capabilities": "A.....",
                    "description": "libvorbis (codec vorbis)"
                },
                "wavesynth": {
                    "capabilities": "A....D",
                    "description": "Wave synthesis pseudo-codec"
                },
                "wavpack": {
                    "capabilities": "AFS..D",
                    "description": "WavPack"
                },
                "ws_snd1": {
                    "capabilities": "A....D",
                    "description": "Westwood Audio (SND1) (codec westwood_snd1)"
                },
                "wmalossless": {
                    "capabilities": "A....D",
                    "description": "Windows Media Audio Lossless"
                },
                "wmapro": {
                    "capabilities": "A....D",
                    "description": "Windows Media Audio 9 Professional"
                },
                "wmav1": {
                    "capabilities": "A....D",
                    "description": "Windows Media Audio 1"
                },
                "wmav2": {
                    "capabilities": "A....D",
                    "description": "Windows Media Audio 2"
                },
                "wmavoice": {
                    "capabilities": "A....D",
                    "description": "Windows Media Audio Voice"
                },
                "xan_dpcm": {
                    "capabilities": "A....D",
                    "description": "DPCM Xan"
                },
                "xma1": {
                    "capabilities": "A....D",
                    "description": "Xbox Media Audio 1"
                },
                "xma2": {
                    "capabilities": "A....D",
                    "description": "Xbox Media Audio 2"
                }
            },
            "subtitle": {
                "ssa": {
                    "capabilities": "S.....",
                    "description": "ASS (Advanced SubStation Alpha) subtitle (codec ass)"
                },
                "ass": {
                    "capabilities": "S.....",
                    "description": "ASS (Advanced SubStation Alpha) subtitle"
                },
                "dvbsub": {
                    "capabilities": "S.....",
                    "description": "DVB subtitles (codec dvb_subtitle)"
                },
                "libzvbi_teletextdec": {
                    "capabilities": "S.....",
                    "description": "Libzvbi DVB teletext decoder (codec dvb_teletext)"
                },
                "dvdsub": {
                    "capabilities": "S.....",
                    "description": "DVD subtitles (codec dvd_subtitle)"
                },
                "cc_dec": {
                    "capabilities": "S.....",
                    "description": "Closed Caption (EIA-608 / CEA-708) (codec eia_608)"
                },
                "pgssub": {
                    "capabilities": "S.....",
                    "description": "HDMV Presentation Graphic Stream subtitles (codec hdmv_pgs_subtitle)"
                },
                "jacosub": {
                    "capabilities": "S.....",
                    "description": "JACOsub subtitle"
                },
                "microdvd": {
                    "capabilities": "S.....",
                    "description": "MicroDVD subtitle"
                },
                "mov_text": {
                    "capabilities": "S.....",
                    "description": "3GPP Timed Text subtitle"
                },
                "mpl2": {
                    "capabilities": "S.....",
                    "description": "MPL2 subtitle"
                },
                "pjs": {
                    "capabilities": "S.....",
                    "description": "PJS subtitle"
                },
                "realtext": {
                    "capabilities": "S.....",
                    "description": "RealText subtitle"
                },
                "sami": {
                    "capabilities": "S.....",
                    "description": "SAMI subtitle"
                },
                "stl": {
                    "capabilities": "S.....",
                    "description": "Spruce subtitle format"
                },
                "srt": {
                    "capabilities": "S.....",
                    "description": "SubRip subtitle (codec subrip)"
                },
                "subrip": {
                    "capabilities": "S.....",
                    "description": "SubRip subtitle"
                },
                "subviewer": {
                    "capabilities": "S.....",
                    "description": "SubViewer subtitle"
                },
                "subviewer1": {
                    "capabilities": "S.....",
                    "description": "SubViewer1 subtitle"
                },
                "text": {
                    "capabilities": "S.....",
                    "description": "Raw text subtitle"
                },
                "vplayer": {
                    "capabilities": "S.....",
                    "description": "VPlayer subtitle"
                },
                "webvtt": {
                    "capabilities": "S.....",
                    "description": "WebVTT subtitle"
                },
                "xsub": {
                    "capabilities": "S.....",
                    "description": "XSUB"
                }
            },
            "video": {
                "012v": {
                    "capabilities": "V....D",
                    "description": "Uncompressed 4:2:2 10-bit"
                },
                "4xm": {
                    "capabilities": "V....D",
                    "description": "4X Movie"
                },
                "8bps": {
                    "capabilities": "V....D",
                    "description": "QuickTime 8BPS video"
                },
                "aasc": {
                    "capabilities": "V....D",
                    "description": "Autodesk RLE"
                },
                "agm": {
                    "capabilities": "V....D",
                    "description": "Amuse Graphics Movie"
                },
                "aic": {
                    "capabilities": "VF...D",
                    "description": "Apple Intermediate Codec"
                },
                "alias_pix": {
                    "capabilities": "V....D",
                    "description": "Alias/Wavefront PIX image"
                },
                "amv": {
                    "capabilities": "V....D",
                    "description": "AMV Video"
                },
                "anm": {
                    "capabilities": "V....D",
                    "description": "Deluxe Paint Animation"
                },
                "ansi": {
                    "capabilities": "V....D",
                    "description": "ASCII/ANSI art"
                },
                "apng": {
                    "capabilities": "VF...D",
                    "description": "APNG (Animated Portable Network Graphics) image"
                },
                "arbc": {
                    "capabilities": "V....D",
                    "description": "Gryphon's Anim Compressor"
                },
                "asv1": {
                    "capabilities": "V....D",
                    "description": "ASUS V1"
                },
                "asv2": {
                    "capabilities": "V....D",
                    "description": "ASUS V2"
                },
                "aura": {
                    "capabilities": "V....D",
                    "description": "Auravision AURA"
                },
                "aura2": {
                    "capabilities": "V....D",
                    "description": "Auravision Aura 2"
                },
                "libdav1d": {
                    "capabilities": "V.....",
                    "description": "dav1d AV1 decoder by VideoLAN (codec av1)"
                },
                "libaom-av1": {
                    "capabilities": "V....D",
                    "description": "libaom AV1 (codec av1)"
                },
                "avrn": {
                    "capabilities": "V.....",
                    "description": "Avid AVI Codec"
                },
                "avrp": {
                    "capabilities": "V....D",
                    "description": "Avid 1:1 10-bit RGB Packer"
                },
                "avs": {
                    "capabilities": "V....D",
                    "description": "AVS (Audio Video Standard) video"
                },
                "avui": {
                    "capabilities": "V....D",
                    "description": "Avid Meridien Uncompressed"
                },
                "ayuv": {
                    "capabilities": "V....D",
                    "description": "Uncompressed packed MS 4:4:4:4"
                },
                "bethsoftvid": {
                    "capabilities": "V....D",
                    "description": "Bethesda VID video"
                },
                "bfi": {
                    "capabilities": "V....D",
                    "description": "Brute Force & Ignorance"
                },
                "binkvideo": {
                    "capabilities": "V....D",
                    "description": "Bink video"
                },
                "bintext": {
                    "capabilities": "V....D",
                    "description": "Binary text"
                },
                "bitpacked": {
                    "capabilities": "V..X..",
                    "description": "Bitpacked"
                },
                "bmp": {
                    "capabilities": "V....D",
                    "description": "BMP (Windows and OS/2 bitmap)"
                },
                "bmv_video": {
                    "capabilities": "V....D",
                    "description": "Discworld II BMV video"
                },
                "brender_pix": {
                    "capabilities": "V....D",
                    "description": "BRender PIX image"
                },
                "c93": {
                    "capabilities": "V....D",
                    "description": "Interplay C93"
                },
                "cavs": {
                    "capabilities": "V....D",
                    "description": "Chinese AVS (Audio Video Standard) (AVS1-P2, JiZhun profile)"
                },
                "cdgraphics": {
                    "capabilities": "V....D",
                    "description": "CD Graphics video"
                },
                "cdtoons": {
                    "capabilities": "V....D",
                    "description": "CDToons video"
                },
                "cdxl": {
                    "capabilities": "V....D",
                    "description": "Commodore CDXL video"
                },
                "cfhd": {
                    "capabilities": "VF...D",
                    "description": "Cineform HD"
                },
                "cinepak": {
                    "capabilities": "V....D",
                    "description": "Cinepak"
                },
                "clearvideo": {
                    "capabilities": "V....D",
                    "description": "Iterated Systems ClearVideo"
                },
                "cljr": {
                    "capabilities": "V....D",
                    "description": "Cirrus Logic AccuPak"
                },
                "cllc": {
                    "capabilities": "VF...D",
                    "description": "Canopus Lossless Codec"
                },
                "eacmv": {
                    "capabilities": "V....D",
                    "description": "Electronic Arts CMV video (codec cmv)"
                },
                "cpia": {
                    "capabilities": "V....D",
                    "description": "CPiA video format"
                },
                "camstudio": {
                    "capabilities": "V....D",
                    "description": "CamStudio (codec cscd)"
                },
                "cyuv": {
                    "capabilities": "V....D",
                    "description": "Creative YUV (CYUV)"
                },
                "dds": {
                    "capabilities": "V.S..D",
                    "description": "DirectDraw Surface image decoder"
                },
                "dfa": {
                    "capabilities": "V....D",
                    "description": "Chronomaster DFA"
                },
                "dirac": {
                    "capabilities": "V.S..D",
                    "description": "BBC Dirac VC-2"
                },
                "dnxhd": {
                    "capabilities": "VFS..D",
                    "description": "VC3/DNxHD"
                },
                "dpx": {
                    "capabilities": "V....D",
                    "description": "DPX (Digital Picture Exchange) image"
                },
                "dsicinvideo": {
                    "capabilities": "V....D",
                    "description": "Delphine Software International CIN video"
                },
                "dvvideo": {
                    "capabilities": "VFS..D",
                    "description": "DV (Digital Video)"
                },
                "dxa": {
                    "capabilities": "V....D",
                    "description": "Feeble Files/ScummVM DXA"
                },
                "dxtory": {
                    "capabilities": "V....D",
                    "description": "Dxtory"
                },
                "dxv": {
                    "capabilities": "VFS..D",
                    "description": "Resolume DXV"
                },
                "escape124": {
                    "capabilities": "V....D",
                    "description": "Escape 124"
                },
                "escape130": {
                    "capabilities": "V....D",
                    "description": "Escape 130"
                },
                "exr": {
                    "capabilities": "VFS..D",
                    "description": "OpenEXR image"
                },
                "ffv1": {
                    "capabilities": "VFS..D",
                    "description": "FFmpeg video codec #1"
                },
                "ffvhuff": {
                    "capabilities": "VF..BD",
                    "description": "Huffyuv FFmpeg variant"
                },
                "fic": {
                    "capabilities": "V.S..D",
                    "description": "Mirillis FIC"
                },
                "fits": {
                    "capabilities": "V....D",
                    "description": "Flexible Image Transport System"
                },
                "flashsv": {
                    "capabilities": "V....D",
                    "description": "Flash Screen Video v1"
                },
                "flashsv2": {
                    "capabilities": "V....D",
                    "description": "Flash Screen Video v2"
                },
                "flic": {
                    "capabilities": "V....D",
                    "description": "Autodesk Animator Flic video"
                },
                "flv": {
                    "capabilities": "V...BD",
                    "description": "FLV / Sorenson Spark / Sorenson H.263 (Flash Video) (codec flv1)"
                },
                "fmvc": {
                    "capabilities": "V....D",
                    "description": "FM Screen Capture Codec"
                },
                "fraps": {
                    "capabilities": "VF...D",
                    "description": "Fraps"
                },
                "frwu": {
                    "capabilities": "V....D",
                    "description": "Forward Uncompressed"
                },
                "g2m": {
                    "capabilities": "V....D",
                    "description": "Go2Meeting"
                },
                "gdv": {
                    "capabilities": "V....D",
                    "description": "Gremlin Digital Video"
                },
                "gif": {
                    "capabilities": "V....D",
                    "description": "GIF (Graphics Interchange Format)"
                },
                "h261": {
                    "capabilities": "V....D",
                    "description": "H.261"
                },
                "h263": {
                    "capabilities": "V...BD",
                    "description": "H.263 / H.263-1996, H.263+ / H.263-1998 / H.263 version 2"
                },
                "h263_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem H.263 decoder wrapper (codec h263)"
                },
                "h263i": {
                    "capabilities": "V...BD",
                    "description": "Intel H.263"
                },
                "h263p": {
                    "capabilities": "V...BD",
                    "description": "H.263 / H.263-1996, H.263+ / H.263-1998 / H.263 version 2"
                },
                "h264": {
                    "capabilities": "VFS..D",
                    "description": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10"
                },
                "h264_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem H.264 decoder wrapper (codec h264)"
                },
                "hap": {
                    "capabilities": "VFS..D",
                    "description": "Vidvox Hap"
                },
                "hevc": {
                    "capabilities": "VFS..D",
                    "description": "HEVC (High Efficiency Video Coding)"
                },
                "hevc_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem HEVC decoder wrapper (codec hevc)"
                },
                "hnm4video": {
                    "capabilities": "V....D",
                    "description": "HNM 4 video"
                },
                "hq_hqa": {
                    "capabilities": "V....D",
                    "description": "Canopus HQ/HQA"
                },
                "hqx": {
                    "capabilities": "VFS..D",
                    "description": "Canopus HQX"
                },
                "huffyuv": {
                    "capabilities": "VF..BD",
                    "description": "Huffyuv / HuffYUV"
                },
                "hymt": {
                    "capabilities": "VF..BD",
                    "description": "HuffYUV MT"
                },
                "idcinvideo": {
                    "capabilities": "V....D",
                    "description": "id Quake II CIN video (codec idcin)"
                },
                "idf": {
                    "capabilities": "V....D",
                    "description": "iCEDraw text"
                },
                "iff": {
                    "capabilities": "V....D",
                    "description": "IFF ACBM/ANIM/DEEP/ILBM/PBM/RGB8/RGBN (codec iff_ilbm)"
                },
                "imm4": {
                    "capabilities": "V....D",
                    "description": "Infinity IMM4"
                },
                "imm5": {
                    "capabilities": "V.....",
                    "description": "Infinity IMM5"
                },
                "indeo2": {
                    "capabilities": "V....D",
                    "description": "Intel Indeo 2"
                },
                "indeo3": {
                    "capabilities": "V....D",
                    "description": "Intel Indeo 3"
                },
                "indeo4": {
                    "capabilities": "V....D",
                    "description": "Intel Indeo Video Interactive 4"
                },
                "indeo5": {
                    "capabilities": "V....D",
                    "description": "Intel Indeo Video Interactive 5"
                },
                "interplayvideo": {
                    "capabilities": "V....D",
                    "description": "Interplay MVE video"
                },
                "jpeg2000": {
                    "capabilities": "VFS..D",
                    "description": "JPEG 2000"
                },
                "libopenjpeg": {
                    "capabilities": "VF...D",
                    "description": "OpenJPEG JPEG 2000 (codec jpeg2000)"
                },
                "jpegls": {
                    "capabilities": "V....D",
                    "description": "JPEG-LS"
                },
                "jv": {
                    "capabilities": "V....D",
                    "description": "Bitmap Brothers JV video"
                },
                "kgv1": {
                    "capabilities": "V....D",
                    "description": "Kega Game Video"
                },
                "kmvc": {
                    "capabilities": "V....D",
                    "description": "Karl Morton's video codec"
                },
                "lagarith": {
                    "capabilities": "VF...D",
                    "description": "Lagarith lossless"
                },
                "loco": {
                    "capabilities": "V....D",
                    "description": "LOCO"
                },
                "lscr": {
                    "capabilities": "V....D",
                    "description": "LEAD Screen Capture"
                },
                "m101": {
                    "capabilities": "V....D",
                    "description": "Matrox Uncompressed SD"
                },
                "eamad": {
                    "capabilities": "V....D",
                    "description": "Electronic Arts Madcow Video (codec mad)"
                },
                "magicyuv": {
                    "capabilities": "VFS..D",
                    "description": "MagicYUV video"
                },
                "mdec": {
                    "capabilities": "VF...D",
                    "description": "Sony PlayStation MDEC (Motion DECoder)"
                },
                "mimic": {
                    "capabilities": "VF...D",
                    "description": "Mimic"
                },
                "mjpeg": {
                    "capabilities": "V....D",
                    "description": "MJPEG (Motion JPEG)"
                },
                "mjpegb": {
                    "capabilities": "V....D",
                    "description": "Apple MJPEG-B"
                },
                "mmvideo": {
                    "capabilities": "V....D",
                    "description": "American Laser Games MM Video"
                },
                "motionpixels": {
                    "capabilities": "V....D",
                    "description": "Motion Pixels video"
                },
                "mpeg1video": {
                    "capabilities": "V.S.BD",
                    "description": "MPEG-1 video"
                },
                "mpeg1_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem MPEG1 decoder wrapper (codec mpeg1video)"
                },
                "mpeg2video": {
                    "capabilities": "V.S.BD",
                    "description": "MPEG-2 video"
                },
                "mpegvideo": {
                    "capabilities": "V.S.BD",
                    "description": "MPEG-1 video (codec mpeg2video)"
                },
                "mpeg2_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem MPEG2 decoder wrapper (codec mpeg2video)"
                },
                "mpeg4": {
                    "capabilities": "VF..BD",
                    "description": "MPEG-4 part 2"
                },
                "mpeg4_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem MPEG4 decoder wrapper (codec mpeg4)"
                },
                "msa1": {
                    "capabilities": "V....D",
                    "description": "MS ATC Screen"
                },
                "mscc": {
                    "capabilities": "V....D",
                    "description": "Mandsoft Screen Capture Codec"
                },
                "msmpeg4v1": {
                    "capabilities": "V...BD",
                    "description": "MPEG-4 part 2 Microsoft variant version 1"
                },
                "msmpeg4v2": {
                    "capabilities": "V...BD",
                    "description": "MPEG-4 part 2 Microsoft variant version 2"
                },
                "msmpeg4": {
                    "capabilities": "V...BD",
                    "description": "MPEG-4 part 2 Microsoft variant version 3 (codec msmpeg4v3)"
                },
                "msrle": {
                    "capabilities": "V....D",
                    "description": "Microsoft RLE"
                },
                "mss1": {
                    "capabilities": "V....D",
                    "description": "MS Screen 1"
                },
                "mss2": {
                    "capabilities": "V....D",
                    "description": "MS Windows Media Video V9 Screen"
                },
                "msvideo1": {
                    "capabilities": "V....D",
                    "description": "Microsoft Video 1"
                },
                "mszh": {
                    "capabilities": "VF...D",
                    "description": "LCL (LossLess Codec Library) MSZH"
                },
                "mts2": {
                    "capabilities": "V....D",
                    "description": "MS Expression Encoder Screen"
                },
                "mv30": {
                    "capabilities": "V....D",
                    "description": "MidiVid 3.0"
                },
                "mvc1": {
                    "capabilities": "V....D",
                    "description": "Silicon Graphics Motion Video Compressor 1"
                },
                "mvc2": {
                    "capabilities": "V....D",
                    "description": "Silicon Graphics Motion Video Compressor 2"
                },
                "mvdv": {
                    "capabilities": "V....D",
                    "description": "MidiVid VQ"
                },
                "mvha": {
                    "capabilities": "V....D",
                    "description": "MidiVid Archive Codec"
                },
                "mwsc": {
                    "capabilities": "V....D",
                    "description": "MatchWare Screen Capture Codec"
                },
                "mxpeg": {
                    "capabilities": "V....D",
                    "description": "Mobotix MxPEG video"
                },
                "notchlc": {
                    "capabilities": "VF...D",
                    "description": "NotchLC"
                },
                "nuv": {
                    "capabilities": "V....D",
                    "description": "NuppelVideo/RTJPEG"
                },
                "paf_video": {
                    "capabilities": "V....D",
                    "description": "Amazing Studio Packed Animation File Video"
                },
                "pam": {
                    "capabilities": "V....D",
                    "description": "PAM (Portable AnyMap) image"
                },
                "pbm": {
                    "capabilities": "V....D",
                    "description": "PBM (Portable BitMap) image"
                },
                "pcx": {
                    "capabilities": "V....D",
                    "description": "PC Paintbrush PCX image"
                },
                "pfm": {
                    "capabilities": "V....D",
                    "description": "PFM (Portable FloatMap) image"
                },
                "pgm": {
                    "capabilities": "V....D",
                    "description": "PGM (Portable GrayMap) image"
                },
                "pgmyuv": {
                    "capabilities": "V....D",
                    "description": "PGMYUV (Portable GrayMap YUV) image"
                },
                "pictor": {
                    "capabilities": "V....D",
                    "description": "Pictor/PC Paint"
                },
                "pixlet": {
                    "capabilities": "VF...D",
                    "description": "Apple Pixlet"
                },
                "png": {
                    "capabilities": "VF...D",
                    "description": "PNG (Portable Network Graphics) image"
                },
                "ppm": {
                    "capabilities": "V....D",
                    "description": "PPM (Portable PixelMap) image"
                },
                "prores": {
                    "capabilities": "VFS..D",
                    "description": "ProRes (iCodec Pro)"
                },
                "prosumer": {
                    "capabilities": "V....D",
                    "description": "Brooktree ProSumer Video"
                },
                "psd": {
                    "capabilities": "VF...D",
                    "description": "Photoshop PSD file"
                },
                "ptx": {
                    "capabilities": "V....D",
                    "description": "V.Flash PTX image"
                },
                "qdraw": {
                    "capabilities": "V....D",
                    "description": "Apple QuickDraw"
                },
                "qpeg": {
                    "capabilities": "V....D",
                    "description": "Q-team QPEG"
                },
                "qtrle": {
                    "capabilities": "V....D",
                    "description": "QuickTime Animation (RLE) video"
                },
                "r10k": {
                    "capabilities": "V....D",
                    "description": "AJA Kona 10-bit RGB Codec"
                },
                "r210": {
                    "capabilities": "V....D",
                    "description": "Uncompressed RGB 10-bit"
                },
                "rasc": {
                    "capabilities": "V....D",
                    "description": "RemotelyAnywhere Screen Capture"
                },
                "rawvideo": {
                    "capabilities": "V.....",
                    "description": "raw video"
                },
                "rl2": {
                    "capabilities": "V....D",
                    "description": "RL2 video"
                },
                "roqvideo": {
                    "capabilities": "V....D",
                    "description": "id RoQ video (codec roq)"
                },
                "rpza": {
                    "capabilities": "V....D",
                    "description": "QuickTime video (RPZA)"
                },
                "rscc": {
                    "capabilities": "V....D",
                    "description": "innoHeim/Rsupport Screen Capture Codec"
                },
                "rv10": {
                    "capabilities": "V....D",
                    "description": "RealVideo 1.0"
                },
                "rv20": {
                    "capabilities": "V....D",
                    "description": "RealVideo 2.0"
                },
                "rv30": {
                    "capabilities": "VF...D",
                    "description": "RealVideo 3.0"
                },
                "rv40": {
                    "capabilities": "VF...D",
                    "description": "RealVideo 4.0"
                },
                "sanm": {
                    "capabilities": "V....D",
                    "description": "LucasArts SANM/Smush video"
                },
                "scpr": {
                    "capabilities": "V....D",
                    "description": "ScreenPressor"
                },
                "screenpresso": {
                    "capabilities": "V....D",
                    "description": "Screenpresso"
                },
                "sgi": {
                    "capabilities": "V....D",
                    "description": "SGI image"
                },
                "sgirle": {
                    "capabilities": "V....D",
                    "description": "Silicon Graphics RLE 8-bit video"
                },
                "sheervideo": {
                    "capabilities": "VF...D",
                    "description": "BitJazz SheerVideo"
                },
                "smackvid": {
                    "capabilities": "V....D",
                    "description": "Smacker video (codec smackvideo)"
                },
                "smc": {
                    "capabilities": "V....D",
                    "description": "QuickTime Graphics (SMC)"
                },
                "smvjpeg": {
                    "capabilities": "V.....",
                    "description": "SMV JPEG"
                },
                "snow": {
                    "capabilities": "V....D",
                    "description": "Snow"
                },
                "sp5x": {
                    "capabilities": "V....D",
                    "description": "Sunplus JPEG (SP5X)"
                },
                "speedhq": {
                    "capabilities": "V....D",
                    "description": "NewTek SpeedHQ"
                },
                "srgc": {
                    "capabilities": "V....D",
                    "description": "Screen Recorder Gold Codec"
                },
                "sunrast": {
                    "capabilities": "V....D",
                    "description": "Sun Rasterfile image"
                },
                "svq1": {
                    "capabilities": "V....D",
                    "description": "Sorenson Vector Quantizer 1 / Sorenson Video 1 / SVQ1"
                },
                "svq3": {
                    "capabilities": "V...BD",
                    "description": "Sorenson Vector Quantizer 3 / Sorenson Video 3 / SVQ3"
                },
                "targa": {
                    "capabilities": "V....D",
                    "description": "Truevision Targa image"
                },
                "targa_y216": {
                    "capabilities": "V....D",
                    "description": "Pinnacle TARGA CineWave YUV16"
                },
                "tdsc": {
                    "capabilities": "V....D",
                    "description": "TDSC"
                },
                "eatgq": {
                    "capabilities": "V....D",
                    "description": "Electronic Arts TGQ video (codec tgq)"
                },
                "eatgv": {
                    "capabilities": "V....D",
                    "description": "Electronic Arts TGV video (codec tgv)"
                },
                "theora": {
                    "capabilities": "VF..BD",
                    "description": "Theora"
                },
                "thp": {
                    "capabilities": "V....D",
                    "description": "Nintendo Gamecube THP video"
                },
                "tiertexseqvideo": {
                    "capabilities": "V....D",
                    "description": "Tiertex Limited SEQ video"
                },
                "tiff": {
                    "capabilities": "VF...D",
                    "description": "TIFF image"
                },
                "tmv": {
                    "capabilities": "V....D",
                    "description": "8088flex TMV"
                },
                "eatqi": {
                    "capabilities": "V....D",
                    "description": "Electronic Arts TQI Video (codec tqi)"
                },
                "truemotion1": {
                    "capabilities": "V....D",
                    "description": "Duck TrueMotion 1.0"
                },
                "truemotion2": {
                    "capabilities": "V....D",
                    "description": "Duck TrueMotion 2.0"
                },
                "truemotion2rt": {
                    "capabilities": "V....D",
                    "description": "Duck TrueMotion 2.0 Real Time"
                },
                "camtasia": {
                    "capabilities": "V....D",
                    "description": "TechSmith Screen Capture Codec (codec tscc)"
                },
                "tscc2": {
                    "capabilities": "V....D",
                    "description": "TechSmith Screen Codec 2"
                },
                "txd": {
                    "capabilities": "V....D",
                    "description": "Renderware TXD (TeXture Dictionary) image"
                },
                "ultimotion": {
                    "capabilities": "V....D",
                    "description": "IBM UltiMotion (codec ulti)"
                },
                "utvideo": {
                    "capabilities": "VF...D",
                    "description": "Ut Video"
                },
                "v210": {
                    "capabilities": "VFS..D",
                    "description": "Uncompressed 4:2:2 10-bit"
                },
                "v210x": {
                    "capabilities": "V....D",
                    "description": "Uncompressed 4:2:2 10-bit"
                },
                "v308": {
                    "capabilities": "V....D",
                    "description": "Uncompressed packed 4:4:4"
                },
                "v408": {
                    "capabilities": "V....D",
                    "description": "Uncompressed packed QT 4:4:4:4"
                },
                "v410": {
                    "capabilities": "VFS..D",
                    "description": "Uncompressed 4:4:4 10-bit"
                },
                "vb": {
                    "capabilities": "V....D",
                    "description": "Beam Software VB"
                },
                "vble": {
                    "capabilities": "VF...D",
                    "description": "VBLE Lossless Codec"
                },
                "vc1": {
                    "capabilities": "V....D",
                    "description": "SMPTE VC-1"
                },
                "vc1_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem VC1 decoder wrapper (codec vc1)"
                },
                "vc1image": {
                    "capabilities": "V....D",
                    "description": "Windows Media Video 9 Image v2"
                },
                "vcr1": {
                    "capabilities": "V....D",
                    "description": "ATI VCR1"
                },
                "xl": {
                    "capabilities": "V....D",
                    "description": "Miro VideoXL (codec vixl)"
                },
                "vmdvideo": {
                    "capabilities": "V....D",
                    "description": "Sierra VMD video"
                },
                "vmnc": {
                    "capabilities": "V....D",
                    "description": "VMware Screen Codec / VMware Video"
                },
                "vp3": {
                    "capabilities": "VF..BD",
                    "description": "On2 VP3"
                },
                "vp4": {
                    "capabilities": "VF..BD",
                    "description": "On2 VP4"
                },
                "vp5": {
                    "capabilities": "V....D",
                    "description": "On2 VP5"
                },
                "vp6": {
                    "capabilities": "V....D",
                    "description": "On2 VP6"
                },
                "vp6a": {
                    "capabilities": "V.S..D",
                    "description": "On2 VP6 (Flash version, with alpha channel)"
                },
                "vp6f": {
                    "capabilities": "V....D",
                    "description": "On2 VP6 (Flash version)"
                },
                "vp7": {
                    "capabilities": "V....D",
                    "description": "On2 VP7"
                },
                "vp8": {
                    "capabilities": "VFS..D",
                    "description": "On2 VP8"
                },
                "vp8_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem VP8 decoder wrapper (codec vp8)"
                },
                "libvpx": {
                    "capabilities": "V....D",
                    "description": "libvpx VP8 (codec vp8)"
                },
                "vp9": {
                    "capabilities": "VFS..D",
                    "description": "Google VP9"
                },
                "vp9_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem VP9 decoder wrapper (codec vp9)"
                },
                "libvpx-vp9": {
                    "capabilities": "V.....",
                    "description": "libvpx VP9 (codec vp9)"
                },
                "wcmv": {
                    "capabilities": "V....D",
                    "description": "WinCAM Motion Video"
                },
                "webp": {
                    "capabilities": "VF...D",
                    "description": "WebP image"
                },
                "wmv1": {
                    "capabilities": "V...BD",
                    "description": "Windows Media Video 7"
                },
                "wmv2": {
                    "capabilities": "V...BD",
                    "description": "Windows Media Video 8"
                },
                "wmv3": {
                    "capabilities": "V....D",
                    "description": "Windows Media Video 9"
                },
                "wmv3image": {
                    "capabilities": "V....D",
                    "description": "Windows Media Video 9 Image"
                },
                "wnv1": {
                    "capabilities": "V....D",
                    "description": "Winnov WNV1"
                },
                "wrapped_avframe": {
                    "capabilities": "V.....",
                    "description": "AVPacket to AVFrame passthrough"
                },
                "vqavideo": {
                    "capabilities": "V....D",
                    "description": "Westwood Studios VQA (Vector Quantized Animation) video (codec ws_vqa)"
                },
                "xan_wc3": {
                    "capabilities": "V....D",
                    "description": "Wing Commander III / Xan"
                },
                "xan_wc4": {
                    "capabilities": "V....D",
                    "description": "Wing Commander IV / Xxan"
                },
                "xbin": {
                    "capabilities": "V....D",
                    "description": "eXtended BINary text"
                },
                "xbm": {
                    "capabilities": "V....D",
                    "description": "XBM (X BitMap) image"
                },
                "xface": {
                    "capabilities": "V.....",
                    "description": "X-face image"
                },
                "xpm": {
                    "capabilities": "V....D",
                    "description": "XPM (X PixMap) image"
                },
                "xwd": {
                    "capabilities": "V....D",
                    "description": "XWD (X Window Dump) image"
                },
                "y41p": {
                    "capabilities": "V....D",
                    "description": "Uncompressed YUV 4:1:1 12-bit"
                },
                "ylc": {
                    "capabilities": "VF...D",
                    "description": "YUY2 Lossless Codec"
                },
                "yop": {
                    "capabilities": "V.....",
                    "description": "Psygnosis YOP Video"
                },
                "yuv4": {
                    "capabilities": "V....D",
                    "description": "Uncompressed packed 4:2:0"
                },
                "zerocodec": {
                    "capabilities": "V....D",
                    "description": "ZeroCodec Lossless Video"
                },
                "zlib": {
                    "capabilities": "VF...D",
                    "description": "LCL (LossLess Codec Library) ZLIB"
                },
                "zmbv": {
                    "capabilities": "V....D",
                    "description": "Zip Motion Blocks Video"
                }
            }
        },
        "encoders": {
            "audio": {
                "aac": {
                    "capabilities": "A.....",
                    "description": "AAC (Advanced Audio Coding)"
                },
                "ac3": {
                    "capabilities": "A.....",
                    "description": "ATSC A/52A (AC-3)"
                },
                "ac3_fixed": {
                    "capabilities": "A.....",
                    "description": "ATSC A/52A (AC-3) (codec ac3)"
                },
                "adpcm_adx": {
                    "capabilities": "A.....",
                    "description": "SEGA CRI ADX ADPCM"
                },
                "g722": {
                    "capabilities": "A.....",
                    "description": "G.722 ADPCM (codec adpcm_g722)"
                },
                "g726": {
                    "capabilities": "A.....",
                    "description": "G.726 ADPCM (codec adpcm_g726)"
                },
                "g726le": {
                    "capabilities": "A.....",
                    "description": "G.726 little endian ADPCM (\"right-justified\") (codec adpcm_g726le)"
                },
                "adpcm_ima_qt": {
                    "capabilities": "A.....",
                    "description": "ADPCM IMA QuickTime"
                },
                "adpcm_ima_ssi": {
                    "capabilities": "A.....",
                    "description": "ADPCM IMA Simon & Schuster Interactive"
                },
                "adpcm_ima_wav": {
                    "capabilities": "A.....",
                    "description": "ADPCM IMA WAV"
                },
                "adpcm_ms": {
                    "capabilities": "A.....",
                    "description": "ADPCM Microsoft"
                },
                "adpcm_swf": {
                    "capabilities": "A.....",
                    "description": "ADPCM Shockwave Flash"
                },
                "adpcm_yamaha": {
                    "capabilities": "A.....",
                    "description": "ADPCM Yamaha"
                },
                "alac": {
                    "capabilities": "A.....",
                    "description": "ALAC (Apple Lossless Audio Codec)"
                },
                "libopencore_amrnb": {
                    "capabilities": "A.....",
                    "description": "OpenCORE AMR-NB (Adaptive Multi-Rate Narrow-Band) (codec amr_nb)"
                },
                "libvo_amrwbenc": {
                    "capabilities": "A.....",
                    "description": "Android VisualOn AMR-WB (Adaptive Multi-Rate Wide-Band) (codec amr_wb)"
                },
                "aptx": {
                    "capabilities": "A.....",
                    "description": "aptX (Audio Processing Technology for Bluetooth)"
                },
                "aptx_hd": {
                    "capabilities": "A.....",
                    "description": "aptX HD (Audio Processing Technology for Bluetooth)"
                },
                "comfortnoise": {
                    "capabilities": "A.....",
                    "description": "RFC 3389 comfort noise generator"
                },
                "dca": {
                    "capabilities": "A..X..",
                    "description": "DCA (DTS Coherent Acoustics) (codec dts)"
                },
                "eac3": {
                    "capabilities": "A.....",
                    "description": "ATSC A/52 E-AC-3"
                },
                "flac": {
                    "capabilities": "A.....",
                    "description": "FLAC (Free Lossless Audio Codec)"
                },
                "g723_1": {
                    "capabilities": "A.....",
                    "description": "G.723.1"
                },
                "mlp": {
                    "capabilities": "A..X..",
                    "description": "MLP (Meridian Lossless Packing)"
                },
                "mp2": {
                    "capabilities": "A.....",
                    "description": "MP2 (MPEG audio layer 2)"
                },
                "mp2fixed": {
                    "capabilities": "A.....",
                    "description": "MP2 fixed point (MPEG audio layer 2) (codec mp2)"
                },
                "libmp3lame": {
                    "capabilities": "A.....",
                    "description": "libmp3lame MP3 (MPEG audio layer 3) (codec mp3)"
                },
                "nellymoser": {
                    "capabilities": "A.....",
                    "description": "Nellymoser Asao"
                },
                "opus": {
                    "capabilities": "A..X..",
                    "description": "Opus"
                },
                "libopus": {
                    "capabilities": "A.....",
                    "description": "libopus Opus (codec opus)"
                },
                "pcm_alaw": {
                    "capabilities": "A.....",
                    "description": "PCM A-law / G.711 A-law"
                },
                "pcm_dvd": {
                    "capabilities": "A.....",
                    "description": "PCM signed 16|20|24-bit big-endian for DVD media"
                },
                "pcm_f32be": {
                    "capabilities": "A.....",
                    "description": "PCM 32-bit floating point big-endian"
                },
                "pcm_f32le": {
                    "capabilities": "A.....",
                    "description": "PCM 32-bit floating point little-endian"
                },
                "pcm_f64be": {
                    "capabilities": "A.....",
                    "description": "PCM 64-bit floating point big-endian"
                },
                "pcm_f64le": {
                    "capabilities": "A.....",
                    "description": "PCM 64-bit floating point little-endian"
                },
                "pcm_mulaw": {
                    "capabilities": "A.....",
                    "description": "PCM mu-law / G.711 mu-law"
                },
                "pcm_s16be": {
                    "capabilities": "A.....",
                    "description": "PCM signed 16-bit big-endian"
                },
                "pcm_s16be_planar": {
                    "capabilities": "A.....",
                    "description": "PCM signed 16-bit big-endian planar"
                },
                "pcm_s16le": {
                    "capabilities": "A.....",
                    "description": "PCM signed 16-bit little-endian"
                },
                "pcm_s16le_planar": {
                    "capabilities": "A.....",
                    "description": "PCM signed 16-bit little-endian planar"
                },
                "pcm_s24be": {
                    "capabilities": "A.....",
                    "description": "PCM signed 24-bit big-endian"
                },
                "pcm_s24daud": {
                    "capabilities": "A.....",
                    "description": "PCM D-Cinema audio signed 24-bit"
                },
                "pcm_s24le": {
                    "capabilities": "A.....",
                    "description": "PCM signed 24-bit little-endian"
                },
                "pcm_s24le_planar": {
                    "capabilities": "A.....",
                    "description": "PCM signed 24-bit little-endian planar"
                },
                "pcm_s32be": {
                    "capabilities": "A.....",
                    "description": "PCM signed 32-bit big-endian"
                },
                "pcm_s32le": {
                    "capabilities": "A.....",
                    "description": "PCM signed 32-bit little-endian"
                },
                "pcm_s32le_planar": {
                    "capabilities": "A.....",
                    "description": "PCM signed 32-bit little-endian planar"
                },
                "pcm_s64be": {
                    "capabilities": "A.....",
                    "description": "PCM signed 64-bit big-endian"
                },
                "pcm_s64le": {
                    "capabilities": "A.....",
                    "description": "PCM signed 64-bit little-endian"
                },
                "pcm_s8": {
                    "capabilities": "A.....",
                    "description": "PCM signed 8-bit"
                },
                "pcm_s8_planar": {
                    "capabilities": "A.....",
                    "description": "PCM signed 8-bit planar"
                },
                "pcm_u16be": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 16-bit big-endian"
                },
                "pcm_u16le": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 16-bit little-endian"
                },
                "pcm_u24be": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 24-bit big-endian"
                },
                "pcm_u24le": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 24-bit little-endian"
                },
                "pcm_u32be": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 32-bit big-endian"
                },
                "pcm_u32le": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 32-bit little-endian"
                },
                "pcm_u8": {
                    "capabilities": "A.....",
                    "description": "PCM unsigned 8-bit"
                },
                "pcm_vidc": {
                    "capabilities": "A.....",
                    "description": "PCM Archimedes VIDC"
                },
                "real_144": {
                    "capabilities": "A.....",
                    "description": "RealAudio 1.0 (14.4K) (codec ra_144)"
                },
                "roq_dpcm": {
                    "capabilities": "A.....",
                    "description": "id RoQ DPCM"
                },
                "s302m": {
                    "capabilities": "A..X..",
                    "description": "SMPTE 302M"
                },
                "sbc": {
                    "capabilities": "A.....",
                    "description": "SBC (low-complexity subband codec)"
                },
                "sonic": {
                    "capabilities": "A..X..",
                    "description": "Sonic"
                },
                "sonicls": {
                    "capabilities": "A..X..",
                    "description": "Sonic lossless"
                },
                "libspeex": {
                    "capabilities": "A.....",
                    "description": "libspeex Speex (codec speex)"
                },
                "truehd": {
                    "capabilities": "A..X..",
                    "description": "TrueHD"
                },
                "tta": {
                    "capabilities": "A.....",
                    "description": "TTA (True Audio)"
                },
                "vorbis": {
                    "capabilities": "A..X..",
                    "description": "Vorbis"
                },
                "libvorbis": {
                    "capabilities": "A.....",
                    "description": "libvorbis (codec vorbis)"
                },
                "wavpack": {
                    "capabilities": "A.....",
                    "description": "WavPack"
                },
                "wmav1": {
                    "capabilities": "A.....",
                    "description": "Windows Media Audio 1"
                },
                "wmav2": {
                    "capabilities": "A.....",
                    "description": "Windows Media Audio 2"
                }
            },
            "subtitle": {
                "ssa": {
                    "capabilities": "S.....",
                    "description": "ASS (Advanced SubStation Alpha) subtitle (codec ass)"
                },
                "ass": {
                    "capabilities": "S.....",
                    "description": "ASS (Advanced SubStation Alpha) subtitle"
                },
                "dvbsub": {
                    "capabilities": "S.....",
                    "description": "DVB subtitles (codec dvb_subtitle)"
                },
                "dvdsub": {
                    "capabilities": "S.....",
                    "description": "DVD subtitles (codec dvd_subtitle)"
                },
                "mov_text": {
                    "capabilities": "S.....",
                    "description": "3GPP Timed Text subtitle"
                },
                "srt": {
                    "capabilities": "S.....",
                    "description": "SubRip subtitle (codec subrip)"
                },
                "subrip": {
                    "capabilities": "S.....",
                    "description": "SubRip subtitle"
                },
                "text": {
                    "capabilities": "S.....",
                    "description": "Raw text subtitle"
                },
                "webvtt": {
                    "capabilities": "S.....",
                    "description": "WebVTT subtitle"
                },
                "xsub": {
                    "capabilities": "S.....",
                    "description": "DivX subtitles (XSUB)"
                }
            },
            "video": {
                "a64multi": {
                    "capabilities": "V.....",
                    "description": "Multicolor charset for Commodore 64 (codec a64_multi)"
                },
                "a64multi5": {
                    "capabilities": "V.....",
                    "description": "Multicolor charset for Commodore 64, extended with 5th color (colram) (codec a64_multi5)"
                },
                "alias_pix": {
                    "capabilities": "V.....",
                    "description": "Alias/Wavefront PIX image"
                },
                "amv": {
                    "capabilities": "V.....",
                    "description": "AMV Video"
                },
                "apng": {
                    "capabilities": "V.....",
                    "description": "APNG (Animated Portable Network Graphics) image"
                },
                "asv1": {
                    "capabilities": "V.....",
                    "description": "ASUS V1"
                },
                "asv2": {
                    "capabilities": "V.....",
                    "description": "ASUS V2"
                },
                "libaom-av1": {
                    "capabilities": "V.....",
                    "description": "libaom AV1 (codec av1)"
                },
                "avrp": {
                    "capabilities": "V.....",
                    "description": "Avid 1:1 10-bit RGB Packer"
                },
                "avui": {
                    "capabilities": "V..X..",
                    "description": "Avid Meridien Uncompressed"
                },
                "ayuv": {
                    "capabilities": "V.....",
                    "description": "Uncompressed packed MS 4:4:4:4"
                },
                "bmp": {
                    "capabilities": "V.....",
                    "description": "BMP (Windows and OS/2 bitmap)"
                },
                "cinepak": {
                    "capabilities": "V.....",
                    "description": "Cinepak"
                },
                "cljr": {
                    "capabilities": "V.....",
                    "description": "Cirrus Logic AccuPak"
                },
                "vc2": {
                    "capabilities": "V.S...",
                    "description": "SMPTE VC-2 (codec dirac)"
                },
                "dnxhd": {
                    "capabilities": "VFS...",
                    "description": "VC3/DNxHD"
                },
                "dpx": {
                    "capabilities": "V.....",
                    "description": "DPX (Digital Picture Exchange) image"
                },
                "dvvideo": {
                    "capabilities": "VFS...",
                    "description": "DV (Digital Video)"
                },
                "ffv1": {
                    "capabilities": "V.S...",
                    "description": "FFmpeg video codec #1"
                },
                "ffvhuff": {
                    "capabilities": "VF....",
                    "description": "Huffyuv FFmpeg variant"
                },
                "fits": {
                    "capabilities": "V.....",
                    "description": "Flexible Image Transport System"
                },
                "flashsv": {
                    "capabilities": "V.....",
                    "description": "Flash Screen Video"
                },
                "flashsv2": {
                    "capabilities": "V.....",
                    "description": "Flash Screen Video Version 2"
                },
                "flv": {
                    "capabilities": "V.....",
                    "description": "FLV / Sorenson Spark / Sorenson H.263 (Flash Video) (codec flv1)"
                },
                "gif": {
                    "capabilities": "V.....",
                    "description": "GIF (Graphics Interchange Format)"
                },
                "h261": {
                    "capabilities": "V.....",
                    "description": "H.261"
                },
                "h263": {
                    "capabilities": "V.....",
                    "description": "H.263 / H.263-1996"
                },
                "h263_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem H.263 encoder wrapper (codec h263)"
                },
                "h263p": {
                    "capabilities": "V.S...",
                    "description": "H.263+ / H.263-1998 / H.263 version 2"
                },
                "libx264": {
                    "capabilities": "V.....",
                    "description": "libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (codec h264)"
                },
                "libx264rgb": {
                    "capabilities": "V.....",
                    "description": "libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 RGB (codec h264)"
                },
                "h264_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem H.264 encoder wrapper (codec h264)"
                },
                "libx265": {
                    "capabilities": "V.....",
                    "description": "libx265 H.265 / HEVC (codec hevc)"
                },
                "hevc_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem HEVC encoder wrapper (codec hevc)"
                },
                "huffyuv": {
                    "capabilities": "VF....",
                    "description": "Huffyuv / HuffYUV"
                },
                "jpeg2000": {
                    "capabilities": "V.....",
                    "description": "JPEG 2000"
                },
                "libopenjpeg": {
                    "capabilities": "VF....",
                    "description": "OpenJPEG JPEG 2000 (codec jpeg2000)"
                },
                "jpegls": {
                    "capabilities": "VF....",
                    "description": "JPEG-LS"
                },
                "ljpeg": {
                    "capabilities": "VF....",
                    "description": "Lossless JPEG"
                },
                "magicyuv": {
                    "capabilities": "VF....",
                    "description": "MagicYUV video"
                },
                "mjpeg": {
                    "capabilities": "VFS...",
                    "description": "MJPEG (Motion JPEG)"
                },
                "mpeg1video": {
                    "capabilities": "V.S...",
                    "description": "MPEG-1 video"
                },
                "mpeg2video": {
                    "capabilities": "V.S...",
                    "description": "MPEG-2 video"
                },
                "mpeg4": {
                    "capabilities": "V.S...",
                    "description": "MPEG-4 part 2"
                },
                "libxvid": {
                    "capabilities": "V.....",
                    "description": "libxvidcore MPEG-4 part 2 (codec mpeg4)"
                },
                "mpeg4_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem MPEG4 encoder wrapper (codec mpeg4)"
                },
                "msmpeg4v2": {
                    "capabilities": "V.....",
                    "description": "MPEG-4 part 2 Microsoft variant version 2"
                },
                "msmpeg4": {
                    "capabilities": "V.....",
                    "description": "MPEG-4 part 2 Microsoft variant version 3 (codec msmpeg4v3)"
                },
                "msvideo1": {
                    "capabilities": "V.....",
                    "description": "Microsoft Video-1"
                },
                "pam": {
                    "capabilities": "V.....",
                    "description": "PAM (Portable AnyMap) image"
                },
                "pbm": {
                    "capabilities": "V.....",
                    "description": "PBM (Portable BitMap) image"
                },
                "pcx": {
                    "capabilities": "V.....",
                    "description": "PC Paintbrush PCX image"
                },
                "pgm": {
                    "capabilities": "V.....",
                    "description": "PGM (Portable GrayMap) image"
                },
                "pgmyuv": {
                    "capabilities": "V.....",
                    "description": "PGMYUV (Portable GrayMap YUV) image"
                },
                "png": {
                    "capabilities": "VF....",
                    "description": "PNG (Portable Network Graphics) image"
                },
                "ppm": {
                    "capabilities": "V.....",
                    "description": "PPM (Portable PixelMap) image"
                },
                "prores": {
                    "capabilities": "VF....",
                    "description": "Apple ProRes"
                },
                "prores_aw": {
                    "capabilities": "VF....",
                    "description": "Apple ProRes (codec prores)"
                },
                "prores_ks": {
                    "capabilities": "VFS...",
                    "description": "Apple ProRes (iCodec Pro) (codec prores)"
                },
                "qtrle": {
                    "capabilities": "V.....",
                    "description": "QuickTime Animation (RLE) video"
                },
                "r10k": {
                    "capabilities": "V.....",
                    "description": "AJA Kona 10-bit RGB Codec"
                },
                "r210": {
                    "capabilities": "V.....",
                    "description": "Uncompressed RGB 10-bit"
                },
                "rawvideo": {
                    "capabilities": "V.....",
                    "description": "raw video"
                },
                "roqvideo": {
                    "capabilities": "V.....",
                    "description": "id RoQ video (codec roq)"
                },
                "rv10": {
                    "capabilities": "V.....",
                    "description": "RealVideo 1.0"
                },
                "rv20": {
                    "capabilities": "V.....",
                    "description": "RealVideo 2.0"
                },
                "sgi": {
                    "capabilities": "V.....",
                    "description": "SGI image"
                },
                "snow": {
                    "capabilities": "V.....",
                    "description": "Snow"
                },
                "sunrast": {
                    "capabilities": "V.....",
                    "description": "Sun Rasterfile image"
                },
                "svq1": {
                    "capabilities": "V.....",
                    "description": "Sorenson Vector Quantizer 1 / Sorenson Video 1 / SVQ1"
                },
                "targa": {
                    "capabilities": "V.....",
                    "description": "Truevision Targa image"
                },
                "libtheora": {
                    "capabilities": "V.....",
                    "description": "libtheora Theora (codec theora)"
                },
                "tiff": {
                    "capabilities": "VF....",
                    "description": "TIFF image"
                },
                "utvideo": {
                    "capabilities": "VF....",
                    "description": "Ut Video"
                },
                "v210": {
                    "capabilities": "V.....",
                    "description": "Uncompressed 4:2:2 10-bit"
                },
                "v308": {
                    "capabilities": "V.....",
                    "description": "Uncompressed packed 4:4:4"
                },
                "v408": {
                    "capabilities": "V.....",
                    "description": "Uncompressed packed QT 4:4:4:4"
                },
                "v410": {
                    "capabilities": "V.....",
                    "description": "Uncompressed 4:4:4 10-bit"
                },
                "libvpx": {
                    "capabilities": "V.....",
                    "description": "libvpx VP8 (codec vp8)"
                },
                "vp8_v4l2m2m": {
                    "capabilities": "V.....",
                    "description": "V4L2 mem2mem VP8 encoder wrapper (codec vp8)"
                },
                "libvpx-vp9": {
                    "capabilities": "V.....",
                    "description": "libvpx VP9 (codec vp9)"
                },
                "libwebp_anim": {
                    "capabilities": "V.....",
                    "description": "libwebp WebP image (codec webp)"
                },
                "libwebp": {
                    "capabilities": "V.....",
                    "description": "libwebp WebP image (codec webp)"
                },
                "wmv1": {
                    "capabilities": "V.....",
                    "description": "Windows Media Video 7"
                },
                "wmv2": {
                    "capabilities": "V.....",
                    "description": "Windows Media Video 8"
                },
                "wrapped_avframe": {
                    "capabilities": "V.....",
                    "description": "AVFrame to AVPacket passthrough"
                },
                "xbm": {
                    "capabilities": "V.....",
                    "description": "XBM (X BitMap) image"
                },
                "xface": {
                    "capabilities": "V.....",
                    "description": "X-face image"
                },
                "xwd": {
                    "capabilities": "V.....",
                    "description": "XWD (X Window Dump) image"
                },
                "y41p": {
                    "capabilities": "V.....",
                    "description": "Uncompressed YUV 4:1:1 12-bit"
                },
                "yuv4": {
                    "capabilities": "V.....",
                    "description": "Uncompressed packed 4:2:0"
                },
                "zlib": {
                    "capabilities": "VF....",
                    "description": "LCL (LossLess Codec Library) ZLIB"
                },
                "zmbv": {
                    "capabilities": "V.....",
                    "description": "Zip Motion Blocks Video"
                }
            }
        }
    },
    "platform": [
        "Linux",
        "nightcrawler",
        "5.8.0-44-generic",
        "#50~20.04.1-Ubuntu SMP Wed Feb 10 21:07:30 UTC 2021",
        "x86_64",
        "x86_64"
    ],
    "python": "3.8.5.final.0"
}
```