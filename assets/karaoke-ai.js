/* NABZ Karaoke AI core: MDX-Net style vocal/instrument separation, runs fully on the user's device.
   Same maths as UVR / audio-separator (hann STFT, centre reflect pad, overlap-add demix).
   Works in the browser (window.NZAI) and in Node for tests (module.exports). */
(function(root){
'use strict';
function radix2(M){var lg=0;while((1<<lg)<M)lg++;var rev=new Uint32Array(M),i,k;for(i=0;i<M;i++){var r=0,x=i;for(k=0;k<lg;k++){r=(r<<1)|(x&1);x>>=1}rev[i]=r}
var c=new Float64Array(M/2),s=new Float64Array(M/2);for(i=0;i<M/2;i++){c[i]=Math.cos(2*Math.PI*i/M);s[i]=Math.sin(2*Math.PI*i/M)}
return function(re,im,inv){var i,j,t;for(i=0;i<M;i++){j=rev[i];if(j>i){t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t}}
for(var size=2;size<=M;size<<=1){var h=size>>1,st=M/size;for(var b=0;b<M;b+=size)for(j=0;j<h;j++){var cc=c[j*st],ss=inv?s[j*st]:-s[j*st],p=b+j,q=p+h,tr=re[q]*cc-im[q]*ss,ti=re[q]*ss+im[q]*cc;re[q]=re[p]-tr;im[q]=im[p]-ti;re[p]+=tr;im[p]+=ti}}}}
/* DFT of any size N (Bluestein when N is not a power of two). inverse is unnormalised. */
function makeDFT(N){if((N&(N-1))===0){var f=radix2(N);return function(re,im,inv){f(re,im,inv)}}
var M=1;while(M<2*N-1)M<<=1;var F=radix2(M),k,wr=new Float64Array(N),wi=new Float64Array(N);
for(k=0;k<N;k++){var a=Math.PI*((k*k)%(2*N))/N;wr[k]=Math.cos(a);wi[k]=-Math.sin(a)}
var br=new Float64Array(M),bi=new Float64Array(M);br[0]=wr[0];bi[0]=-wi[0];for(k=1;k<N;k++){br[k]=br[M-k]=wr[k];bi[k]=bi[M-k]=-wi[k]}F(br,bi,false);
var ar=new Float64Array(M),ai=new Float64Array(M);
return function(re,im,inv){ar.fill(0);ai.fill(0);var sg=inv?-1:1;
for(k=0;k<N;k++){var x=re[k],y=im[k]*sg;ar[k]=x*wr[k]-y*wi[k];ai[k]=x*wi[k]+y*wr[k]}
F(ar,ai,false);for(k=0;k<M;k++){var r=ar[k]*br[k]-ai[k]*bi[k];ai[k]=ar[k]*bi[k]+ai[k]*br[k];ar[k]=r}F(ar,ai,true);
for(k=0;k<N;k++){var u=ar[k]/M,v=ai[k]/M;re[k]=u*wr[k]-v*wi[k];im[k]=(u*wi[k]+v*wr[k])*sg}}}
function Engine(cfg){var N=cfg.n_fft,H=cfg.hop,F=cfg.dim_f,T=cfg.dim_t,C=H*(T-1),P=N/2,K=N/2,i;
var dft=makeDFT(N),win=new Float64Array(N);for(i=0;i<N;i++)win[i]=0.5-0.5*Math.cos(2*Math.PI*i/N);
var re=new Float64Array(N),im=new Float64Array(N),spec=new Float32Array(4*F*T);
var yL=new Float64Array(C+N),yR=new Float64Array(C+N),env=new Float64Array(C+N);
for(var t=0;t<T;t++)for(i=0;i<N;i++)env[t*H+i]+=win[i]*win[i];
function rf(x,j){var k=j-P;if(k<0)k=-k;if(k>=C)k=2*(C-1)-k;return x[k]}
this.chunk=C;this.trim=P;
this.stft=function(cl,cr){var t,n,f,FT=F*T;for(t=0;t<T;t++){var s0=t*H;for(n=0;n<N;n++){re[n]=rf(cl,s0+n)*win[n];im[n]=rf(cr,s0+n)*win[n]}dft(re,im,false);
for(f=0;f<F;f++){var m=(N-f)%N,o=f*T+t;if(f<3){spec[o]=spec[FT+o]=spec[2*FT+o]=spec[3*FT+o]=0;continue}
spec[o]=(re[f]+re[m])/2;spec[FT+o]=(im[f]-im[m])/2;spec[2*FT+o]=(im[f]+im[m])/2;spec[3*FT+o]=(re[m]-re[f])/2}}return spec};
this.istft=function(sp,outL,outR){var t,f,n,FT=F*T;yL.fill(0);yR.fill(0);
for(t=0;t<T;t++){re.fill(0);im.fill(0);
for(f=0;f<=K&&f<F;f++){var o=f*T+t,a=sp[o],b=sp[FT+o],c=sp[2*FT+o],d=sp[3*FT+o];if(f===0||f===K){b=0;d=0}
re[f]=a-d;im[f]=b+c;if(f>0&&f<K){re[N-f]=a+d;im[N-f]=-b+c}}
dft(re,im,true);var s0=t*H;for(n=0;n<N;n++){yL[s0+n]+=re[n]/N*win[n];yR[s0+n]+=im[n]/N*win[n]}}
for(n=0;n<C;n++){var e=env[n+P];outL[n]=e>1e-11?yL[n+P]/e:0;outR[n]=e>1e-11?yR[n+P]/e:0}}}
/* opts: {L,R,cfg,run:async(Float32Array,dims)=>Float32Array, overlap, onProgress(done,total), shouldStop()} */
async function separate(o){var cfg=o.cfg,L=o.L,R=o.R,len=L.length,E=new Engine(cfg),C=E.chunk,tr=E.trim,gen=C-2*tr,ov=o.overlap==null?0.25:o.overlap;
var pad=gen+tr-(len%gen),Lm=tr+len+pad,step=Math.max(1,Math.floor((1-ov)*C)),rL=new Float32Array(Lm),rR=new Float32Array(Lm),dv=new Float32Array(Lm);
var cl=new Float32Array(C),cr=new Float32Array(C),ol=new Float32Array(C),orr=new Float32Array(C),dims=[1,4,cfg.dim_f,cfg.dim_t],total=Math.ceil(Lm/step),done=0,i,n;
for(i=0;i<Lm;i+=step){var end=Math.min(i+C,Lm),act=end-i;
for(n=0;n<C;n++){var j=i+n-tr;var ok=n<act&&j>=0&&j<len;cl[n]=ok?L[j]:0;cr[n]=ok?R[j]:0}
var sp=E.stft(cl,cr),out=await o.run(sp,dims);E.istft(out,ol,orr);
for(n=0;n<act;n++){var w=act>1?(0.5-0.5*Math.cos(2*Math.PI*n/(act-1))):1;rL[i+n]+=ol[n]*w;rR[i+n]+=orr[n]*w;dv[i+n]+=w}
done++;if(o.onProgress)o.onProgress(done,total);if(o.shouldStop&&o.shouldStop())throw new Error('stopped')}
for(n=tr;n<tr+len;n++){var d=dv[n];rL[n]=d>1e-8?rL[n]/d:0;rR[n]=d>1e-8?rR[n]/d:0}dv=null;
var pL=rL.subarray(tr,tr+len),pR=rR.subarray(tr,tr+len),k=cfg.compensate||1,sL=o.inPlace?L:new Float32Array(len),sR=o.inPlace?R:new Float32Array(len);
/* the other stem = mix - model stem (inPlace reuses the input arrays to save memory on phones) */
if(R===L&&o.inPlace){sR=new Float32Array(len)}
for(n=0;n<len;n++){var a=L[n]-pL[n]*k,b=R[n]-pR[n]*k;sL[n]=a;sR[n]=b}
var instr=/instrument/i.test(cfg.primary||'Instrumental');
return instr?{instL:pL,instR:pR,vocL:sL,vocR:sR}:{instL:sL,instR:sR,vocL:pL,vocR:pR}}
var api={separate:separate,makeDFT:makeDFT,Engine:Engine};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NZAI=api;
})(typeof window!=='undefined'?window:this);
