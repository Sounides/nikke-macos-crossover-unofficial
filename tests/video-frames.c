// SPDX-License-Identifier: LGPL-2.1-or-later
#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
static HRESULT inspect_frame(ID3D11Device *d, ID3D11DeviceContext *ctx, IMFSample *s, unsigned *content)
{
 IMFMediaBuffer *b=NULL;IMFDXGIBuffer *gb=NULL;ID3D11Texture2D *t=NULL,*rb=NULL;IDXGIResource *r=NULL;
 ID3D11ShaderResourceView *view=NULL;D3D11_TEXTURE2D_DESC desc;D3D11_MAPPED_SUBRESOURCE map;
 HANDLE h=(HANDLE)(UINT_PTR)0xdeadbeef;HRESULT hr;unsigned nonzero=0,alpha_zero=0;uint64_t sum=0;
 hr=IMFSample_GetBufferByIndex(s,0,&b);if(FAILED(hr))goto end;
 hr=IMFMediaBuffer_QueryInterface(b,&IID_IMFDXGIBuffer,(void**)&gb);printf("dxgi_buffer=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 hr=IMFDXGIBuffer_GetResource(gb,&IID_ID3D11Texture2D,(void**)&t);if(FAILED(hr))goto end;
 ID3D11Texture2D_GetDesc(t,&desc);printf("surface=%ux%u format=%u usage=%u misc=%x\n",desc.Width,desc.Height,desc.Format,desc.Usage,desc.MiscFlags);
 hr=ID3D11Texture2D_QueryInterface(t,&IID_IDXGIResource,(void**)&r);if(FAILED(hr))goto end;
 hr=IDXGIResource_GetSharedHandle(r,&h);printf("shared_query=%08lx null=%u\n",(unsigned long)hr,!h);if(FAILED(hr))goto end;
 hr=ID3D11Device_CreateShaderResourceView(d,(ID3D11Resource*)t,NULL,&view);printf("shader_view=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=desc.MiscFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
 hr=ID3D11Device_CreateTexture2D(d,&desc,NULL,&rb);if(FAILED(hr))goto end;
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)rb,(ID3D11Resource*)t);
 hr=ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)rb,0,D3D11_MAP_READ,0,&map);printf("readback=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 for(unsigned y=0;y<desc.Height;y+=16)for(unsigned x=0;x<desc.Width;x+=16){uint32_t v;memcpy(&v,(BYTE*)map.pData+y*map.RowPitch+x*4,4);sum+=v;nonzero+=!!(v&0xffffff);alpha_zero+=!(v>>24);}
 ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)rb,0);
 printf("rgb_nonzero=%u alpha_zero=%u pixel_sum=%llu\n",nonzero,alpha_zero,(unsigned long long)sum);*content=nonzero;
end:
 if(view)ID3D11ShaderResourceView_Release(view);if(r)IDXGIResource_Release(r);if(rb)ID3D11Texture2D_Release(rb);if(t)ID3D11Texture2D_Release(t);if(gb)IMFDXGIBuffer_Release(gb);if(b)IMFMediaBuffer_Release(b);return hr;
}
int wmain(int argc, WCHAR **argv)
{
 ID3D11Device *d=NULL;ID3D11DeviceContext *ctx=NULL;IMFDXGIDeviceManager *mgr=NULL;
 IMFAttributes *a=NULL;IMFSourceReader *r=NULL;IMFMediaType *mt=NULL;UINT token;HRESULT hr;unsigned frames=0;
 if(argc!=2){fprintf(stderr,"Usage: video-frames.exe VIDEO.mp4\n");return 2;}
 CoInitializeEx(NULL,COINIT_MULTITHREADED);hr=MFStartup(MF_VERSION,MFSTARTUP_FULL);if(FAILED(hr))return 1;
 hr=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,D3D11_CREATE_DEVICE_BGRA_SUPPORT,NULL,0,D3D11_SDK_VERSION,&d,NULL,&ctx);printf("device=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 hr=MFCreateDXGIDeviceManager(&token,&mgr);if(SUCCEEDED(hr))hr=IMFDXGIDeviceManager_ResetDevice(mgr,(IUnknown*)d,token);if(FAILED(hr))goto end;
 hr=MFCreateAttributes(&a,2);if(SUCCEEDED(hr))hr=IMFAttributes_SetUnknown(a,&MF_SOURCE_READER_D3D_MANAGER,(IUnknown*)mgr);
 if(SUCCEEDED(hr))hr=IMFAttributes_SetUINT32(a,&MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING,TRUE);
 if(SUCCEEDED(hr))hr=MFCreateSourceReaderFromURL(argv[1],a,&r);
 printf("reader=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 hr=MFCreateMediaType(&mt);if(SUCCEEDED(hr))hr=IMFMediaType_SetGUID(mt,&MF_MT_MAJOR_TYPE,&MFMediaType_Video);if(SUCCEEDED(hr))hr=IMFMediaType_SetGUID(mt,&MF_MT_SUBTYPE,&MFVideoFormat_ARGB32);
 if(SUCCEEDED(hr))hr=IMFSourceReader_SetCurrentMediaType(r,MF_SOURCE_READER_FIRST_VIDEO_STREAM,NULL,mt);printf("type=%08lx\n",(unsigned long)hr);if(FAILED(hr))goto end;
 for(unsigned i=0;i<20&&frames<3;i++){DWORD flags=0;LONGLONG ts;IMFSample *s=NULL;unsigned nonzero=0;
  hr=IMFSourceReader_ReadSample(r,MF_SOURCE_READER_FIRST_VIDEO_STREAM,0,NULL,&flags,&ts,&s);if(SUCCEEDED(hr)&&s){hr=inspect_frame(d,ctx,s,&nonzero);if(SUCCEEDED(hr)&&nonzero)frames++;IMFSample_Release(s);}if(FAILED(hr)||(flags&MF_SOURCE_READERF_ENDOFSTREAM))break;
 }
end:
 if(mt)IMFMediaType_Release(mt);if(r)IMFSourceReader_Release(r);if(a)IMFAttributes_Release(a);if(mgr)IMFDXGIDeviceManager_Release(mgr);if(ctx)ID3D11DeviceContext_Release(ctx);if(d)ID3D11Device_Release(d);MFShutdown();CoUninitialize();printf("gpu_content_frames=%u\n",frames);return frames==3?0:2;
}
