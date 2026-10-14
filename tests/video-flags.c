// SPDX-License-Identifier: LGPL-2.1-or-later
#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <stdio.h>
int main(void){ID3D11Device*d=NULL;ID3D11DeviceContext*c=NULL;HRESULT h;
h=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,D3D11_CREATE_DEVICE_VIDEO_SUPPORT|D3D11_CREATE_DEVICE_BGRA_SUPPORT,NULL,0,D3D11_SDK_VERSION,&d,NULL,&c);
printf("video_device_hr=%08lx device_null=%u context_null=%u\n",(unsigned long)h,!d,!c);
if(c)ID3D11DeviceContext_Release(c);if(d)ID3D11Device_Release(d);d=NULL;c=NULL;
h=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,D3D11_CREATE_DEVICE_BGRA_SUPPORT,NULL,0,D3D11_SDK_VERSION,&d,NULL,&c);
printf("ordinary_device_hr=%08lx device_valid=%u context_valid=%u\n",(unsigned long)h,!!d,!!c);
if(c)ID3D11DeviceContext_Release(c);if(d)ID3D11Device_Release(d);return FAILED(h);}
