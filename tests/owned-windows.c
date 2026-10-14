/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Owned regression fixture: all window operations target only our own windows.
 * The launcher basename exercises Wine's configured DPI override; no vendor code.
 */
#define WINVER 0x0A00
#define _WIN32_WINNT 0x0A00
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
static HWND edges[4];
static void phase(const char *value) {FILE*f=fopen("C:\\window-fixture\\phase.txt","w");if(f){fputs(value,f);fclose(f);}}
static int command(void){int value=-1;FILE*f=fopen("C:\\window-fixture\\command.txt","r");if(f){fscanf(f,"%d",&value);fclose(f);}return value;}
static LRESULT CALLBACK proc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_PAINT){PAINTSTRUCT paint;HDC dc=BeginPaint(hwnd,&paint);RECT r;GetClientRect(hwnd,&r);HBRUSH a=CreateSolidBrush(RGB(255,0,0)),b=CreateSolidBrush(RGB(0,0,255));RECT l=r;l.right/=2;FillRect(dc,&r,b);FillRect(dc,&l,a);DeleteObject(a);DeleteObject(b);for(int x=0;x<r.right;x++){HPEN p=CreatePen(PS_SOLID,1,(x%2)?RGB(255,255,255):0);HGDIOBJ old=SelectObject(dc,p);MoveToEx(dc,x,r.bottom-40,NULL);LineTo(dc,x,r.bottom);SelectObject(dc,old);DeleteObject(p);}EndPaint(hwnd,&paint);return 0;}
 if(msg==WM_CLOSE){DestroyWindow(hwnd);return 0;}if(msg==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProcW(hwnd,msg,wp,lp);
}
static void position_edges(HWND root, int show_first){RECT r;GetWindowRect(root,&r);int x=r.left,y=r.top,w=r.right-r.left,h=r.bottom-r.top;int d[4][4]={{x-4,y-4,4,h+8},{x,y-4,w,4},{x+w,y-4,4,h+8},{x,y+h,w,4}};for(int i=0;i<4;i++)SetWindowPos(edges[i],0,d[i][0],d[i][1],d[i][2],d[i][3],SWP_NOZORDER|SWP_NOACTIVATE|((i || show_first)?SWP_SHOWWINDOW:0));}
int main(int argc, char **argv){
 SetProcessDPIAware();
 if(argc==2 && !strcmp(argv[1],"--dpi-probe")){
  FILE*f=fopen("C:\\window-fixture\\dpi-probe.txt","w");if(!f)return 2;
  int aware=GetAwarenessFromDpiAwarenessContext(GetThreadDpiAwarenessContext());
  fprintf(f,"dpi=%u awareness=%d\n",GetDpiForSystem(),aware);fclose(f);return 0;
 }
 WNDCLASSW wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandleW(0);wc.lpszClassName=L"OwnedMinimizeFixture";RegisterClassW(&wc);
 HWND root=CreateWindowExW(0,wc.lpszClassName,L"Owned window regression",WS_POPUP|WS_VISIBLE|WS_MINIMIZEBOX,100,120,600,360,0,0,wc.hInstance,0);
 for(int i=0;i<4;i++){edges[i]=CreateWindowExW(WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE|WS_EX_LAYERED,wc.lpszClassName,L"Owned shadow",WS_POPUP|WS_VISIBLE|WS_MINIMIZEBOX,0,0,1,1,root,0,wc.hInstance,0);SetLayeredWindowAttributes(edges[i],0,120,LWA_ALPHA);}
 position_edges(root,1);RECT r;GetClientRect(root,&r);printf("normal dpi=%u awareness=%d client=%ldx%ld screen=%dx%d\n",GetDpiForWindow(root),GetAwarenessFromDpiAwarenessContext(GetWindowDpiAwarenessContext(root)),r.right,r.bottom,GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN));fflush(stdout);phase("normal");
 int state=0;ULONGLONG start=GetTickCount64();MSG msg;
 while(GetTickCount64()-start<120000){
  while(PeekMessageW(&msg,0,0,0,PM_REMOVE)){if(msg.message==WM_QUIT)return 0;TranslateMessage(&msg);DispatchMessageW(&msg);}
  int cmd=command();
  if(state==0 && cmd==1){ShowWindow(root,SW_MINIMIZE);position_edges(root,1);phase("minimized");state=1;}
  if(state==1 && cmd==2){ShowWindow(edges[0],SW_HIDE);ShowWindow(root,SW_RESTORE);position_edges(root,0);phase("restored");state=2;}
  if(cmd==3){for(int i=0;i<4;i++)DestroyWindow(edges[i]);DestroyWindow(root);return 0;}
  Sleep(10);
 }
 return 4;
}
