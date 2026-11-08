#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <d3d12.h>
#include <ddraw.h>
#include <mmsystem.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static LRESULT CALLBACK window_proc(HWND h, UINT msg, WPARAM w, LPARAM l) {
    if (msg == WM_CHAR) printf("PROTON_LAB character=%lu\n", (unsigned long)w);
    if (msg == WM_CLOSE) { DestroyWindow(h); return 0; }
    return DefWindowProcW(h, msg, w, l);
}
int main(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "d3d11";
    const char *output = getenv("PROTON_LAB_OUTPUT");
    if (output && !freopen(output, "w", stdout)) return 19;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("PROTON_LAB bits=%u mode=%s\n", (unsigned)(sizeof(void*)*8), mode);
    WNDCLASSW wc = {0}; wc.lpfnWndProc=window_proc; wc.hInstance=GetModuleHandleW(NULL); wc.lpszClassName=L"ProtonLab";
    if (!RegisterClassW(&wc)) return 10;
    HWND window = CreateWindowW(L"ProtonLab", L"Proton lab unattended fixture", WS_OVERLAPPEDWINDOW|WS_VISIBLE, 50, 50, 800, 600, NULL, NULL, wc.hInstance, NULL);
    if (!window) return 11;
    PostMessageW(window, WM_CHAR, L'A', 0);
    if (!strcmp(mode,"d3d12")) {
        ID3D12Device *device=NULL;
        HRESULT hr=D3D12CreateDevice(NULL,D3D_FEATURE_LEVEL_11_0,&IID_ID3D12Device,(void**)&device);
        printf("PROTON_LAB d3d12_device=0x%08lx\n", (unsigned long)hr);
        if (device) ID3D12Device_Release(device);
        DestroyWindow(window); return FAILED(hr)?12:0;
    }
    if (!strcmp(mode,"ddraw")) {
        IDirectDraw *dd=NULL;
        HRESULT hr=DirectDrawCreate(NULL,&dd,NULL);
        if (dd) { hr=IDirectDraw_SetCooperativeLevel(dd,window,DDSCL_NORMAL); IDirectDraw_Release(dd); }
        printf("PROTON_LAB ddraw=0x%08lx\n",(unsigned long)hr);
        DestroyWindow(window); return FAILED(hr)?13:0;
    }
    if (!strcmp(mode,"audio")) {
        WAVEFORMATEX format={WAVE_FORMAT_PCM,2,48000,192000,4,16,0}; HWAVEOUT out=NULL;
        MMRESULT result=waveOutOpen(&out,WAVE_MAPPER,&format,0,0,CALLBACK_NULL);
        printf("PROTON_LAB audio_open=%u\n",(unsigned)result);
        if (out) waveOutClose(out);
        DestroyWindow(window); return result?14:0;
    }
    DXGI_SWAP_CHAIN_DESC desc={0}; desc.BufferDesc.Width=800;desc.BufferDesc.Height=600;desc.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
    desc.SampleDesc.Count=1;desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;desc.BufferCount=2;desc.OutputWindow=window;desc.Windowed=TRUE;desc.SwapEffect=DXGI_SWAP_EFFECT_DISCARD;
    ID3D11Device *device=NULL; ID3D11DeviceContext *context=NULL; IDXGISwapChain *swap=NULL;
    HRESULT hr=D3D11CreateDeviceAndSwapChain(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,0,NULL,0,D3D11_SDK_VERSION,&desc,&swap,&device,NULL,&context);
    if (FAILED(hr)) { printf("PROTON_LAB d3d11_error=0x%08lx\n",(unsigned long)hr); DestroyWindow(window);return 15; }
    ID3D11Texture2D *buffer=NULL; ID3D11RenderTargetView *view=NULL;
    hr=IDXGISwapChain_GetBuffer(swap,0,&IID_ID3D11Texture2D,(void**)&buffer);
    if (FAILED(hr)) return 16;
    hr=ID3D11Device_CreateRenderTargetView(device,(ID3D11Resource*)buffer,NULL,&view);
    if (FAILED(hr)) return 17;
    LARGE_INTEGER freq,before,after; QueryPerformanceFrequency(&freq);
    for (int i=0;i<240;i++) {
        MSG msg; while (PeekMessageW(&msg,NULL,0,0,PM_REMOVE)) { TranslateMessage(&msg);DispatchMessageW(&msg); }
        QueryPerformanceCounter(&before);
        float color[]={0.1f,(float)(i%60)/60.0f,0.3f,1.0f};
        ID3D11DeviceContext_ClearRenderTargetView(context,view,color);
        hr=IDXGISwapChain_Present(swap,1,0);
        QueryPerformanceCounter(&after);
        if (FAILED(hr)) return 18;
        printf("PROTON_LAB frame_ms=%.6f\n",1000.0*(double)(after.QuadPart-before.QuadPart)/(double)freq.QuadPart);
    }
    printf("PROTON_LAB d3d11_presented=240\n");
    ID3D11RenderTargetView_Release(view);ID3D11Texture2D_Release(buffer);IDXGISwapChain_Release(swap);ID3D11DeviceContext_Release(context);ID3D11Device_Release(device);DestroyWindow(window);
    return 0;
}
