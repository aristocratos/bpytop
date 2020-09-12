# GPU Monitor Specs

Should display: 

- GPU Name
- GPU Temperature
- GPU Power Usage
- GPU Load %
- MEM Load %
- 'clocks' (please specify)
- 'vram usage' (please specify)

# Where It May Be Found

each `hwmon#` directory has a series of useful infos which may be parsed.

driver? name (i have `amdgpu`)
/sys/class/drm/card0/device/hwmon/hwmon0/name

current fan rpm can be found:
/sys/class/drm/card0/device/hwmon/hwmon0/fan1_input

freq label and value:
/sys/class/drm/card0/device/hwmon/hwmon0/freq1_label
/sys/class/drm/card0/device/hwmon/hwmon0/freq1_input

set power (VDDGFX):
/sys/class/drm/card0/device/hwmon/hwmon0/in0_label
/sys/class/drm/card0/device/hwmon/hwmon0/in0_input

temp (also has label? 'edge' on mine):
/sys/class/drm/card0/device/hwmon/hwmon0/temp1_label
/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input

avg power (in W):
/sys/class/drm/card0/device/hwmon/hwmon0/power1_average

mem load %:
/sys/class/drm/card0/device/mem_busy_percent

gpu load %:
/sys/class/drm/card0/device/gpu_busy_percent

mem GTT total/used:
/sys/class/drm/card0/device/mem_info_gtt_used
/sys/class/drm/card0/device/mem_info_gtt_total

mem VRAM total/used:
/sys/class/drm/card0/device/mem_info_vram_used
/sys/class/drm/card0/device/mem_info_vram_total

potential:
chosen MCLK:
/sys/class/drm/card0/device/pp_dpm_mclk
chosen SCLK:
/sys/class/drm/card0/device/pp_dpm_sclk
