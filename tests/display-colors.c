/* SPDX-License-Identifier: LGPL-2.1-or-later */
#ifndef DISPLAY_CHECK_DURATION_MS
#define DISPLAY_CHECK_DURATION_MS 600000
#endif
#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <stdio.h>
static LRESULT CALLBACK proc(HWND w,UINT m,WPARAM a,LPARAM b){if(m==WM_CLOSE){DestroyWindow(w);return 0;} if(m==WM_DESTROY){PostQuitMessage(0);return 0;} return DefWindowProcW(w,m,a,b);}
int main(void){ SetProcessDPIAware();
 WNDCLASSW cls={0};cls.lpfnWndProc=proc;cls.hInstance=GetModuleHandleW(0);cls.lpszClassName=L"NikkeColorCheck";RegisterClassW(&cls);
 RECT rect={0,0,1024,512};AdjustWindowRect(&rect,WS_OVERLAPPEDWINDOW,0);HWND hwnd=CreateWindowW(cls.lpszClassName,L"NIKKE SDR Color Check",WS_OVERLAPPEDWINDOW|WS_VISIBLE,100,100,rect.right-rect.left,rect.bottom-rect.top,0,0,cls.hInstance,0);
 ID3D11Device*d=0;ID3D11DeviceContext*c=0;IDXGISwapChain*swap=0;ID3D11Texture2D*buf=0;ID3D11RenderTargetView*rt=0;
 DXGI_SWAP_CHAIN_DESC sd={0};sd.BufferDesc.Width=1024;sd.BufferDesc.Height=512;sd.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sd.SampleDesc.Count=1;sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sd.BufferCount=2;sd.OutputWindow=hwnd;sd.Windowed=1;sd.SwapEffect=DXGI_SWAP_EFFECT_DISCARD;
 HRESULT hr=D3D11CreateDeviceAndSwapChain(0,D3D_DRIVER_TYPE_HARDWARE,0,0,0,0,D3D11_SDK_VERSION,&sd,&swap,&d,0,&c);if(FAILED(hr))return 2;
 IDXGISwapChain_GetBuffer(swap,0,&IID_ID3D11Texture2D,(void**)&buf);ID3D11Device_CreateRenderTargetView(d,(ID3D11Resource*)buf,0,&rt);
 const char *vs="float4 main(uint id:SV_VertexID):SV_Position {float2 p[3]={float2(-1,-1),float2(-1,3),float2(3,-1)};return float4(p[id],0,1);}";
 const char *ps="float4 main(float4 p:SV_Position):SV_Target {if(p.y>=256)return float4(((uint)p.x%2),((uint)p.x%2),((uint)p.x%2),1);uint n=(uint)p.x/128;float v[8]={0,16./255,64./255,128./255,192./255,235./255,1,1};if(p.y>=128){if(n<2)return float4(1,0,0,1);if(n<4)return float4(0,1,0,1);if(n<6)return float4(0,0,1,1);return float4(1,1,1,1);}return float4(v[n],v[n],v[n],1);}";
 ID3DBlob*b=0;ID3D11VertexShader*v=0;ID3D11PixelShader*p=0;if(FAILED(D3DCompile(vs,strlen(vs),0,0,0,"main","vs_4_0",0,0,&b,0)))return 3;ID3D11Device_CreateVertexShader(d,ID3D10Blob_GetBufferPointer(b),ID3D10Blob_GetBufferSize(b),0,&v);ID3D10Blob_Release(b);
 if(FAILED(D3DCompile(ps,strlen(ps),0,0,0,"main","ps_4_0",0,0,&b,0)))return 4;ID3D11Device_CreatePixelShader(d,ID3D10Blob_GetBufferPointer(b),ID3D10Blob_GetBufferSize(b),0,&p);ID3D10Blob_Release(b);
 ID3D11DeviceContext_OMSetRenderTargets(c,1,&rt,0);D3D11_VIEWPORT viewport={0,0,1024,512,0,1};ID3D11DeviceContext_RSSetViewports(c,1,&viewport);ID3D11DeviceContext_IASetPrimitiveTopology(c,D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);ID3D11DeviceContext_VSSetShader(c,v,0,0);ID3D11DeviceContext_PSSetShader(c,p,0,0);
 MSG msg;ULONGLONG start=GetTickCount64();while(GetTickCount64()-start<DISPLAY_CHECK_DURATION_MS){while(PeekMessageW(&msg,0,0,0,PM_REMOVE)){if(msg.message==WM_QUIT)return 0;TranslateMessage(&msg);DispatchMessageW(&msg);}ID3D11DeviceContext_Draw(c,3,0);IDXGISwapChain_Present(swap,1,0);}
 return 0;
}
