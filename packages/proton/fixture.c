#define WIDL_C_INLINE_WRAPPERS
#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_6.h>
#include <d3d12.h>
#include <ddraw.h>
#include <mmsystem.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static IDXGISwapChain *window_swap=NULL;
static int window_fullscreen=0;
static LRESULT CALLBACK window_proc(HWND h, UINT msg, WPARAM w, LPARAM l) {
    if (msg == WM_SETFOCUS) printf("PROTON_LAB focus_gained=%p\n",(void*)h);
    if (msg == WM_KILLFOCUS) printf("PROTON_LAB focus_lost=%p\n",(void*)h);
    if (msg == WM_SIZE) printf("PROTON_LAB client_size=%ux%u\n",(unsigned)LOWORD(l),(unsigned)HIWORD(l));
    if (msg == WM_KEYDOWN) {
        printf("PROTON_LAB key_down=%lu\n",(unsigned long)w);
        if (w==VK_F11 && window_swap) {
            HRESULT hr=IDXGISwapChain_SetFullscreenState(window_swap,!window_fullscreen,NULL);
            if (SUCCEEDED(hr)) window_fullscreen=!window_fullscreen;
            printf("PROTON_LAB fullscreen=%d hresult=0x%08lx\n",window_fullscreen,(unsigned long)hr);
        }
    }
    if (msg == WM_CHAR) printf("PROTON_LAB character=%lu\n", (unsigned long)w);
    if (msg == WM_CLOSE) { DestroyWindow(h); return 0; }
    return DefWindowProcW(h, msg, w, l);
}
static int render_d3d12(HWND window) {
    ID3D12Device *device=NULL;
    ID3D12CommandQueue *queue=NULL;
    ID3D12CommandAllocator *allocator=NULL;
    ID3D12GraphicsCommandList *list=NULL;
    ID3D12DescriptorHeap *heap=NULL;
    ID3D12Fence *fence=NULL;
    ID3D12Resource *buffers[2]={NULL,NULL};
    IDXGIFactory4 *factory=NULL;
    IDXGISwapChain1 *swap1=NULL;
    IDXGISwapChain3 *swap=NULL;
    HANDLE event=NULL;
    HRESULT hr=S_OK;
#define CHECK_D12(call) do { hr=(call); if(FAILED(hr)) goto done; } while(0)
    CHECK_D12(D3D12CreateDevice(NULL,D3D_FEATURE_LEVEL_11_0,&IID_ID3D12Device,(void**)&device));
    printf("PROTON_LAB d3d12_device=0x%08lx\n",(unsigned long)hr);
    D3D12_COMMAND_QUEUE_DESC queue_desc={0};
    queue_desc.Type=D3D12_COMMAND_LIST_TYPE_DIRECT;
    CHECK_D12(ID3D12Device_CreateCommandQueue(device,&queue_desc,&IID_ID3D12CommandQueue,(void**)&queue));
    CHECK_D12(CreateDXGIFactory1(&IID_IDXGIFactory4,(void**)&factory));
    DXGI_SWAP_CHAIN_DESC1 swap_desc={0};
    swap_desc.Width=800;swap_desc.Height=600;swap_desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
    swap_desc.SampleDesc.Count=1;swap_desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;
    swap_desc.BufferCount=2;swap_desc.SwapEffect=DXGI_SWAP_EFFECT_FLIP_DISCARD;
    CHECK_D12(IDXGIFactory4_CreateSwapChainForHwnd(factory,(IUnknown*)queue,window,&swap_desc,NULL,NULL,&swap1));
    CHECK_D12(IDXGISwapChain1_QueryInterface(swap1,&IID_IDXGISwapChain3,(void**)&swap));
    D3D12_DESCRIPTOR_HEAP_DESC heap_desc={0};
    heap_desc.Type=D3D12_DESCRIPTOR_HEAP_TYPE_RTV;heap_desc.NumDescriptors=2;
    CHECK_D12(ID3D12Device_CreateDescriptorHeap(device,&heap_desc,&IID_ID3D12DescriptorHeap,(void**)&heap));
    D3D12_CPU_DESCRIPTOR_HANDLE start=ID3D12DescriptorHeap_GetCPUDescriptorHandleForHeapStart(heap);
    UINT stride=ID3D12Device_GetDescriptorHandleIncrementSize(device,D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
    for (UINT i=0;i<2;i++) {
        CHECK_D12(IDXGISwapChain3_GetBuffer(swap,i,&IID_ID3D12Resource,(void**)&buffers[i]));
        D3D12_CPU_DESCRIPTOR_HANDLE handle=start;handle.ptr+=i*stride;
        ID3D12Device_CreateRenderTargetView(device,buffers[i],NULL,handle);
    }
    CHECK_D12(ID3D12Device_CreateCommandAllocator(device,D3D12_COMMAND_LIST_TYPE_DIRECT,&IID_ID3D12CommandAllocator,(void**)&allocator));
    CHECK_D12(ID3D12Device_CreateCommandList(device,0,D3D12_COMMAND_LIST_TYPE_DIRECT,allocator,NULL,&IID_ID3D12GraphicsCommandList,(void**)&list));
    CHECK_D12(ID3D12GraphicsCommandList_Close(list));
    CHECK_D12(ID3D12Device_CreateFence(device,0,D3D12_FENCE_FLAG_NONE,&IID_ID3D12Fence,(void**)&fence));
    event=CreateEventW(NULL,FALSE,FALSE,NULL);
    if (!event) {hr=E_FAIL;goto done;}
    LARGE_INTEGER frequency,before,after;QueryPerformanceFrequency(&frequency);
    for (UINT64 frame=1;frame<=240;frame++) {
        MSG msg;while(PeekMessageW(&msg,NULL,0,0,PM_REMOVE)) {TranslateMessage(&msg);DispatchMessageW(&msg);}
        QueryPerformanceCounter(&before);
        UINT index=IDXGISwapChain3_GetCurrentBackBufferIndex(swap);
        CHECK_D12(ID3D12CommandAllocator_Reset(allocator));
        CHECK_D12(ID3D12GraphicsCommandList_Reset(list,allocator,NULL));
        D3D12_RESOURCE_BARRIER barrier={0};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
        barrier.Transition.pResource=buffers[index];barrier.Transition.Subresource=D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
        barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_PRESENT;barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_RENDER_TARGET;
        ID3D12GraphicsCommandList_ResourceBarrier(list,1,&barrier);
        D3D12_CPU_DESCRIPTOR_HANDLE handle=start;handle.ptr+=index*stride;
        float color[]={0.3f,(float)(frame%60)/60.0f,0.1f,1.0f};
        ID3D12GraphicsCommandList_ClearRenderTargetView(list,handle,color,0,NULL);
        barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_RENDER_TARGET;barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_PRESENT;
        ID3D12GraphicsCommandList_ResourceBarrier(list,1,&barrier);
        CHECK_D12(ID3D12GraphicsCommandList_Close(list));
        ID3D12CommandList *commands[]={(ID3D12CommandList*)list};
        ID3D12CommandQueue_ExecuteCommandLists(queue,1,commands);
        CHECK_D12(IDXGISwapChain3_Present(swap,1,0));
        CHECK_D12(ID3D12CommandQueue_Signal(queue,fence,frame));
        if(ID3D12Fence_GetCompletedValue(fence)<frame) {
            CHECK_D12(ID3D12Fence_SetEventOnCompletion(fence,frame,event));
            if(WaitForSingleObject(event,10000)!=WAIT_OBJECT_0) {hr=E_FAIL;goto done;}
        }
        QueryPerformanceCounter(&after);
        printf("PROTON_LAB frame_ms=%.6f\n",1000.0*(double)(after.QuadPart-before.QuadPart)/(double)frequency.QuadPart);
    }
    printf("PROTON_LAB d3d12_presented=240\n");
done:
    printf("PROTON_LAB d3d12_result=0x%08lx\n",(unsigned long)hr);
    if(event) CloseHandle(event);
    if(fence) ID3D12Fence_Release(fence);
    if(list) ID3D12GraphicsCommandList_Release(list);
    if(allocator) ID3D12CommandAllocator_Release(allocator);
    if(heap) ID3D12DescriptorHeap_Release(heap);
    for(int i=0;i<2;i++) if(buffers[i]) ID3D12Resource_Release(buffers[i]);
    if(swap) IDXGISwapChain3_Release(swap);
    if(swap1) IDXGISwapChain1_Release(swap1);
    if(factory) IDXGIFactory4_Release(factory);
    if(queue) ID3D12CommandQueue_Release(queue);
    if(device) ID3D12Device_Release(device);
#undef CHECK_D12
    return FAILED(hr)?12:0;
}

static int run_fixture(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "d3d11";
    const char *output = getenv("PROTON_LAB_OUTPUT");
    if (output && !freopen(output, "w", stdout)) return 19;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("PROTON_LAB bits=%u mode=%s\n", (unsigned)(sizeof(void*)*8), mode);
    if (!strcmp(mode,"fail")) return 23;
    WNDCLASSW wc = {0}; wc.lpfnWndProc=window_proc; wc.hInstance=GetModuleHandleW(NULL); wc.lpszClassName=L"ProtonLab";wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
    if (!RegisterClassW(&wc)) { printf("PROTON_LAB register_class_error=%lu\n",(unsigned long)GetLastError()); return 10; }
    HWND window = CreateWindowW(L"ProtonLab", L"Proton lab unattended fixture", WS_OVERLAPPEDWINDOW|WS_VISIBLE, 50, 50, 800, 600, NULL, NULL, wc.hInstance, NULL);
    if (!window) { printf("PROTON_LAB create_window_error=%lu\n",(unsigned long)GetLastError()); return 11; }
    PostMessageW(window, WM_CHAR, L'A', 0);
    if (!strcmp(mode,"d3d12")) {
        int result=render_d3d12(window);
        DestroyWindow(window); return result;
    }
    if (!strcmp(mode,"ddraw")) {
        IDirectDraw *dd=NULL;
        IDirectDrawSurface *surface=NULL;
        HRESULT hr=DirectDrawCreate(NULL,&dd,NULL);
        if (SUCCEEDED(hr)) hr=IDirectDraw_SetCooperativeLevel(dd,window,DDSCL_NORMAL);
        DDSURFACEDESC desc={0}; desc.dwSize=sizeof(desc);
        desc.dwFlags=DDSD_CAPS|DDSD_WIDTH|DDSD_HEIGHT|DDSD_PIXELFORMAT;
        desc.dwWidth=64;desc.dwHeight=64;desc.ddsCaps.dwCaps=DDSCAPS_OFFSCREENPLAIN|DDSCAPS_SYSTEMMEMORY;
        desc.ddpfPixelFormat.dwSize=sizeof(desc.ddpfPixelFormat);desc.ddpfPixelFormat.dwFlags=DDPF_RGB;
        desc.ddpfPixelFormat.dwRGBBitCount=32;desc.ddpfPixelFormat.dwRBitMask=0xff0000;
        desc.ddpfPixelFormat.dwGBitMask=0xff00;desc.ddpfPixelFormat.dwBBitMask=0xff;
        if (SUCCEEDED(hr)) hr=IDirectDraw_CreateSurface(dd,&desc,&surface,NULL);
        DDBLTFX fill={0};fill.dwSize=sizeof(fill);fill.dwFillColor=0x123456;
        if (SUCCEEDED(hr)) hr=IDirectDrawSurface_Blt(surface,NULL,NULL,NULL,DDBLT_COLORFILL|DDBLT_WAIT,&fill);
        DDSURFACEDESC locked={0};locked.dwSize=sizeof(locked);
        if (SUCCEEDED(hr)) {
            hr=IDirectDrawSurface_Lock(surface,NULL,&locked,DDLOCK_WAIT|DDLOCK_READONLY,NULL);
            if (SUCCEEDED(hr)) {
                int clear=1;
                for (unsigned y=0;y<64;y++) for(unsigned x=0;x<64;x++)
                    if ((((DWORD*)((unsigned char*)locked.lpSurface+y*locked.lPitch))[x]&0xffffff)!=0x123456) clear=0;
                IDirectDrawSurface_Unlock(surface,NULL);
                printf("PROTON_LAB ddraw_surface_readback=%d\n",clear);
                if (!clear) hr=E_FAIL;
            }
        }
        if (surface) IDirectDrawSurface_Release(surface);
        if (dd) IDirectDraw_Release(dd);
        printf("PROTON_LAB ddraw=0x%08lx\n",(unsigned long)hr);
        DestroyWindow(window); return FAILED(hr)?13:0;
    }
    if (!strcmp(mode,"audio")) {
        WAVEFORMATEX format={WAVE_FORMAT_PCM,2,48000,192000,4,16,0}; HWAVEOUT out=NULL;
        MMRESULT result=waveOutOpen(&out,WAVE_MAPPER,&format,0,0,CALLBACK_NULL);
        printf("PROTON_LAB audio_open=%u\n",(unsigned)result);
        short silence[48000*2]={0};
        WAVEHDR header={0};header.lpData=(char*)silence;header.dwBufferLength=sizeof(silence);
        if (!result) result=waveOutPrepareHeader(out,&header,sizeof(header));
        if (!result) result=waveOutWrite(out,&header,sizeof(header));
        if (!result) {
            for (int i=0;i<300 && !(header.dwFlags&WHDR_DONE);i++) Sleep(10);
            printf("PROTON_LAB audio_buffer_done=%d\n",!!(header.dwFlags&WHDR_DONE));
            if (!(header.dwFlags&WHDR_DONE)) result=MMSYSERR_ERROR;
        }
        if (out) {
            waveOutReset(out);waveOutUnprepareHeader(out,&header,sizeof(header));waveOutClose(out);
        }
        DestroyWindow(window); return result?14:0;
    }
    int hdr = !strcmp(mode, "hdr");
    int fullscreen = !strcmp(mode,"fullscreen") || hdr;
    int frames = !strcmp(mode,"window") ? 1800 : 240;
    HWND peer=NULL;
    if (!strcmp(mode,"window")) {
        peer=CreateWindowW(L"ProtonLab",L"Proton lab focus peer",WS_OVERLAPPEDWINDOW|WS_VISIBLE,100,100,300,200,NULL,NULL,wc.hInstance,NULL);
        if (peer) UpdateWindow(peer);
    }
    DXGI_SWAP_CHAIN_DESC desc={0}; desc.BufferDesc.Width=800;desc.BufferDesc.Height=600;desc.BufferDesc.Format=hdr?DXGI_FORMAT_R10G10B10A2_UNORM:DXGI_FORMAT_R8G8B8A8_UNORM;
    desc.SampleDesc.Count=1;desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;desc.BufferCount=2;desc.OutputWindow=window;desc.Windowed=TRUE;desc.SwapEffect=hdr?DXGI_SWAP_EFFECT_FLIP_DISCARD:DXGI_SWAP_EFFECT_DISCARD;
    ID3D11Device *device=NULL; ID3D11DeviceContext *context=NULL; IDXGISwapChain *swap=NULL;
    HRESULT hr=D3D11CreateDeviceAndSwapChain(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,0,NULL,0,D3D11_SDK_VERSION,&desc,&swap,&device,NULL,&context);
    if (FAILED(hr)) { printf("PROTON_LAB d3d11_error=0x%08lx\n",(unsigned long)hr); DestroyWindow(window);return 15; }
    window_swap=swap;
    if (fullscreen) {
        HRESULT full_hr=IDXGISwapChain_SetFullscreenState(swap,TRUE,NULL);
        if (SUCCEEDED(full_hr)) window_fullscreen=1;
        printf("PROTON_LAB fullscreen=%d hresult=0x%08lx\n",window_fullscreen,(unsigned long)full_hr);
    }
    if (hdr) {
        IDXGISwapChain3 *swap3=NULL;
        UINT support=0;
        hr=IDXGISwapChain_QueryInterface(swap,&IID_IDXGISwapChain3,(void**)&swap3);
        if (SUCCEEDED(hr)) hr=IDXGISwapChain3_CheckColorSpaceSupport(swap3,DXGI_COLOR_SPACE_RGB_FULL_G2084_NONE_P2020,&support);
        printf("PROTON_LAB hdr_present_support=%u hresult=0x%08lx\n",(unsigned)(support&DXGI_SWAP_CHAIN_COLOR_SPACE_SUPPORT_FLAG_PRESENT),(unsigned long)hr);
        if (FAILED(hr) || !(support&DXGI_SWAP_CHAIN_COLOR_SPACE_SUPPORT_FLAG_PRESENT)) {
            if (swap3) IDXGISwapChain3_Release(swap3);
            if(window_fullscreen) IDXGISwapChain_SetFullscreenState(swap,FALSE,NULL);
            window_swap=NULL;
            IDXGISwapChain_Release(swap);ID3D11DeviceContext_Release(context);ID3D11Device_Release(device);DestroyWindow(window);
            return 0;
        }
        hr=IDXGISwapChain3_SetColorSpace1(swap3,DXGI_COLOR_SPACE_RGB_FULL_G2084_NONE_P2020);
        IDXGISwapChain3_Release(swap3);
        if (FAILED(hr)) return 20;
        printf("PROTON_LAB hdr_colorspace_set=1\n");
    }
    ID3D11Texture2D *buffer=NULL; ID3D11RenderTargetView *view=NULL;
    hr=IDXGISwapChain_GetBuffer(swap,0,&IID_ID3D11Texture2D,(void**)&buffer);
    if (FAILED(hr)) return 16;
    hr=ID3D11Device_CreateRenderTargetView(device,(ID3D11Resource*)buffer,NULL,&view);
    if (FAILED(hr)) return 17;
    LARGE_INTEGER freq,before,after; QueryPerformanceFrequency(&freq);
    for (int i=0;i<frames;i++) {
        MSG msg; while (PeekMessageW(&msg,NULL,0,0,PM_REMOVE)) { TranslateMessage(&msg);DispatchMessageW(&msg); }
        QueryPerformanceCounter(&before);
        float color[]={0.1f,(float)(i%60)/60.0f,0.3f,1.0f};
        ID3D11DeviceContext_ClearRenderTargetView(context,view,color);
        hr=IDXGISwapChain_Present(swap,1,0);
        QueryPerformanceCounter(&after);
        if (FAILED(hr)) return 18;
        printf("PROTON_LAB frame_ms=%.6f\n",1000.0*(double)(after.QuadPart-before.QuadPart)/(double)freq.QuadPart);
    }
    printf("PROTON_LAB d3d11_presented=%d\n",frames);
    if(window_fullscreen) IDXGISwapChain_SetFullscreenState(swap,FALSE,NULL);
    window_swap=NULL;
    if(peer) DestroyWindow(peer);
    ID3D11RenderTargetView_Release(view);ID3D11Texture2D_Release(buffer);IDXGISwapChain_Release(swap);ID3D11DeviceContext_Release(context);ID3D11Device_Release(device);DestroyWindow(window);
    return 0;
}

int main(int argc, char **argv) {
    int result=run_fixture(argc,argv);
    printf("PROTON_LAB result=%d\n",result);
    return result;
}
