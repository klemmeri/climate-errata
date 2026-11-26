import numpy as np
from scipy.stats import norm, gamma
rng=np.random.default_rng(20261125)
n=128; dx=2.0  # km, 256 km domain
L=25.0
k=np.fft.fftfreq(n,d=dx); K2=k[:,None]**2+k[None,:]**2
S=(1+(2*np.pi)**2*K2*L**2)**(-1.5)   # 2-D exponential-like covariance spectrum
amp=np.sqrt(S)
p_dry=0.6; z0=norm.ppf(p_dry); g=gamma(0.8,scale=12.0)   # wet amounts mm
sizes=[0,10,26,50,100]   # km box side (0 = point)
c=n//2
res={s:[] for s in sizes}
for d in range(6000):
    z=np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((n,n)))*amp)); z/=z.std(); z=0.7*rng.standard_normal()+np.sqrt(1-0.49)*z
    r=np.where(z>z0, g.ppf((norm.cdf(z)-p_dry)/(1-p_dry)),0.0)
    for s in sizes:
        h=max(1,int(round(s/dx)))//2
        res[s].append(r[c,c] if s==0 else r[c-h:c+h,c-h:c+h].mean())
out={}
for s in sizes:
    x=np.array(res[s]); out[s]=dict(mean=x.mean(),wet=(x>=0.1).mean(),sd=x.std(),p99=np.quantile(x,.99),p999=np.quantile(x,.999))
    print(s,{k:round(v,3) for k,v in out[s].items()})
import json; json.dump({str(k):v for k,v in out.items()},open('res.json','w'),indent=1)
