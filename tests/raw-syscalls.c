// SPDX-License-Identifier: LGPL-2.1-or-later
#include <windows.h>
#include <winternl.h>
#include <stdio.h>
#include <string.h>
static void *direct(const char*n){BYTE *nt=(BYTE*)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),n),*p;BYTE code[]={0x4c,0x8b,0xd1,0xb8,0,0,0,0,0x0f,0x05,0xc3};if(!nt||nt[0]!=0x4c||nt[3]!=0xb8)return NULL;memcpy(code+4,nt+4,4);p=VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(p)memcpy(p,code,sizeof(code));return p;}
int main(void){LONG(WINAPI *set)(HANDLE,LONG*);LONG(WINAPI *timefn)(LARGE_INTEGER*);LONG(WINAPI *query)(HANDLE,void*,int,void*,SIZE_T,SIZE_T*);HANDLE e;LONG prev=-1,hr;LARGE_INTEGER t={0};MEMORY_BASIC_INFORMATION m={0};SIZE_T bytes=0;unsigned checks=0;
set=direct("NtSetEvent");timefn=direct("NtQuerySystemTime");query=direct("NtQueryVirtualMemory");if(!set||!timefn||!query)return 1;
e=CreateEventW(NULL,FALSE,FALSE,NULL);hr=set(e,&prev);checks+=hr==0&&prev==0&&WaitForSingleObject(e,0)==WAIT_OBJECT_0;printf("event_status=%08lx checks=%u\n",(unsigned long)hr,checks);
hr=set((HANDLE)(UINT_PTR)0xdeadbeef,&prev);checks+=hr==(LONG)0xc0000008;printf("invalid_handle_status=%08lx checks=%u\n",(unsigned long)hr,checks);
hr=timefn(&t);checks+=hr==0&&t.QuadPart>0;printf("time_status=%08lx time_valid=%u checks=%u\n",(unsigned long)hr,t.QuadPart>0,checks);
hr=query(GetCurrentProcess(),(void*)set,0,&m,sizeof(m),&bytes);checks+=hr==0&&bytes==sizeof(m)&&m.AllocationBase==(void*)set&&m.State==MEM_COMMIT;printf("memory_status=%08lx size=%llu allocation_valid=%u checks=%u\n",(unsigned long)hr,(unsigned long long)bytes,m.AllocationBase==(void*)set,checks);
CloseHandle(e);VirtualFree((void*)set,0,MEM_RELEASE);VirtualFree((void*)timefn,0,MEM_RELEASE);VirtualFree((void*)query,0,MEM_RELEASE);return checks==4?0:2;}
