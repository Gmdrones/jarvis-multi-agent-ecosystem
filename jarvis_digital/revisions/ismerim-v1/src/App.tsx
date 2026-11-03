import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {ArrowUpRight,ArrowDown,Menu,X,MapPin,Play} from 'lucide-react';
import {COMPANY_DATA as C, POSTS as P, SERVICOS as S} from './data';

function Media({post,hero=false}:{post:typeof P[number],hero?:boolean}){
  const ref=useRef<HTMLDivElement>(null);
  const url='https://www.instagram.com/'+post.kind+'/'+post.id+'/';
  useEffect(()=>{
    const el=ref.current;if(!el)return;
    const fit=()=>{
      const w=el.clientWidth,h=el.clientHeight;
      const mediaW=Math.max(w,h*post.aspect)*(hero?1.18:1.14);
      const iframeW=post.kind==='reel'?mediaW/(.5625/.8):mediaW;
      const mediaH=mediaW/post.aspect;
      el.style.setProperty('--iw',iframeW+'px');
      el.style.setProperty('--ix',(hero&&w<600?(w-iframeW)*.90:(w-iframeW)/2)+'px');
      el.style.setProperty('--iy',-(54+(mediaH-h)*post.y)+'px');
      el.style.setProperty('--ih',(54+mediaH+260)+'px');
      el.querySelectorAll('iframe').forEach(f=>{f.title=post.title;f.tabIndex=-1});
    };
    fit();
    const resize=new ResizeObserver(fit);
    resize.observe(el);
    const mutation=new MutationObserver(fit);
    mutation.observe(el,{childList:true});
    return()=>{resize.disconnect();mutation.disconnect()};
  },[post,hero]);

  return (
    <div className={'media-mask '+(hero?'hero-media':'')} ref={ref} data-media={post.id} aria-label={post.title}>
      <blockquote className="instagram-media" data-instgrm-permalink={url} data-instgrm-version="14">
        <a href={url} target="_blank" rel="noreferrer">Abrir {post.title}</a>
      </blockquote>
    </div>
  );
}

export default function App(){
  const [menu,setMenu]=useState(false);
  const menuButton=useRef<HTMLButtonElement>(null);
  const mobileNav=useRef<HTMLElement>(null);

  useLayoutEffect(()=>{
    if(menu)mobileNav.current?.querySelector<HTMLAnchorElement>('a')?.focus();
  },[menu]);

  useEffect(()=>{
    const close=(e:KeyboardEvent)=>{
      if(e.key==='Escape'&&document.getElementById('mobile-nav')){
        setMenu(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener('keydown',close);
    const script=document.createElement('script');
    script.src='https://www.instagram.com/embed.js';
    script.async=true;
    document.body.appendChild(script);
    return()=>{
      window.removeEventListener('keydown',close);
      script.remove();
    };
  },[]);

  return (
    <>
      <a className="skip" href="#conteudo">Pular para o conteúdo</a>
      <div className="demo-bar">
        <span>Demonstração não oficial · em revisão</span>
        <span>Ismerim Barbearia · Jarvis Digital</span>
      </div>

      <header>
        <a className="wordmark" href="#inicio">
          ISMERIM <b>BARBEARIA</b>
          <small>SHOPPING NOVO LEBLON</small>
        </a>
        <nav className="desktop-nav" aria-label="Navegação principal">
          <a href="#trabalhos">Nosso trabalho</a>
          <a href="#servicos">Serviços</a>
          <a href="#contato">Localização</a>
        </nav>
        <a className="header-contact" href={C.whatsappUrl} target="_blank" rel="noreferrer">
          Agende seu horário <ArrowUpRight size={16}/>
        </a>
        <button 
          ref={menuButton} 
          className="menu-toggle" 
          aria-label={menu?'Fechar menu':'Abrir menu'} 
          aria-expanded={menu} 
          aria-controls="mobile-nav" 
          onClick={()=>setMenu(!menu)}
        >
          {menu?<X/>:<Menu/>}
        </button>
      </header>

      {menu && (
        <nav ref={mobileNav} id="mobile-nav" className="mobile-nav" aria-label="Navegação móvel">
          {[
            ['Nosso trabalho','#trabalhos'],
            ['Serviços','#servicos'],
            ['Localização','#contato']
          ].map(([text,href])=>(
            <a href={href} key={href} onClick={()=>setMenu(false)}>
              {text}<ArrowUpRight/>
            </a>
          ))}
        </nav>
      )}

      <main id="conteudo">
        <section id="inicio" className="hero">
          <div className="hero-visual">
            <Media post={P[0]} hero/>
          </div>
          <div className="hero-wash"/>
          <div className="hero-content">
            <p className="eyebrow">BARRA DA TIJUCA · SHOPPING NOVO LEBLON LOJA 140</p>
            <h1>Seu estilo.<br/><em>Seu momento.</em></h1>
            <p className="hero-intro">
              Family barber contemporânea com atendimento acolhedor.<br/>
              Corte, barba e cuidado completo para todas as idades na Barra.
            </p>
            <a className="button" href={C.whatsappUrl} target="_blank" rel="noreferrer">
              Agende pelo WhatsApp <ArrowUpRight size={18}/>
            </a>
          </div>
          <div className="hero-bottom">
            <span>CABELO · BARBA · INFANTIL</span>
            <a href="#trabalhos">CONHEÇA OS TRABALHOS <ArrowDown size={16}/></a>
          </div>
        </section>

        <section id="trabalhos" className="gallery section-pad">
          <div className="section-label">
            <span>01 — NOSSO DIA A DIA</span>
            <span>ISMERIM BARBEARIA / RIO DE JANEIRO</span>
          </div>
          <div className="gallery-heading">
            <h2>Precisão real,<br/><em>em movimento.</em></h2>
            <p>
              Vídeos autênticos registrados no dia a dia da barbearia.<br/>
              Cuidado dedicado e atenção a cada pessoa.
            </p>
          </div>
          <div className="gallery-grid">
            <article className="work work-video">
              <div className="media-container">
                <Media post={P[1]}/>
                <div className="video-hint">
                  <Play size={12} fill="currentColor"/> TOQUE PARA ASSISTIR
                </div>
              </div>
              <div className="work-label">
                <h3>{P[1].title}</h3>
                <span>01 / INFANTIL</span>
              </div>
              <a 
                className="accessible-original" 
                href={'https://www.instagram.com/reel/'+P[1].id+'/'} 
                target="_blank" 
                rel="noreferrer"
              >
                Abrir vídeo original <ArrowUpRight size={13}/>
              </a>
            </article>

            <article className="work work-video">
              <div className="media-container">
                <Media post={P[2]}/>
                <div className="video-hint">
                  <Play size={12} fill="currentColor"/> TOQUE PARA ASSISTIR
                </div>
              </div>
              <div className="work-label">
                <h3>{P[2].title}</h3>
                <span>02 / ADULTO</span>
              </div>
              <a 
                className="accessible-original" 
                href={'https://www.instagram.com/reel/'+P[2].id+'/'} 
                target="_blank" 
                rel="noreferrer"
              >
                Abrir vídeo original <ArrowUpRight size={13}/>
              </a>
            </article>
          </div>
        </section>

        <section id="servicos" className="services section-pad">
          <div className="section-label">
            <span>02 — ATENDIMENTO DEDICADO</span>
            <span>CUIDADO COMPLETO</span>
          </div>
          <div className="services-grid">
            <div>
              <p className="eyebrow">ESTRUTURA & FAMÍLIA</p>
              <h2>Experiência feita<br/><em>para você.</em></h2>
              <p className="section-copy">
                Um espaço acolhedor no Shopping Novo Leblon.<br/>
                Cabelo, barba e atendimento infantil.
              </p>
            </div>
            <div className="service-rows">
              {S.map((s,i)=>(
                <a href={C.whatsappUrl} target="_blank" rel="noreferrer" key={s.nome}>
                  <span>0{i+1}</span>
                  <div>
                    <h3>{s.nome}</h3>
                    <p className="text-xs text-sand-muted mt-1">{s.desc}</p>
                  </div>
                  <ArrowUpRight size={22}/>
                </a>
              ))}
            </div>
          </div>
        </section>

        <section id="contato" className="contact section-pad">
          <div className="section-label">
            <span>03 — LOCALIZAÇÃO</span>
            <span>SHOPPING NOVO LEBLON</span>
          </div>
          <div className="contact-grid">
            <div>
              <p className="eyebrow">BARRA DA TIJUCA</p>
              <h2>Esperamos<br/><em>sua visita.</em></h2>
              <a className="button dark" href={C.whatsappUrl} target="_blank" rel="noreferrer">
                Falar com a Barbearia <ArrowUpRight size={18}/>
              </a>
            </div>
            <div className="address">
              <MapPin size={26} strokeWidth={1}/>
              <h3>{C.name}</h3>
              <p>
                {C.address}<br/>
                {C.neighborhood} · {C.city}, RJ<br/>
                Av. das Américas · Barra da Tijuca
              </p>
              <a className="text-link" href={C.mapsUrl} target="_blank" rel="noreferrer">
                Abrir no Google Maps <ArrowUpRight size={15}/>
              </a>
              <a className="phone" href={'tel:+'+C.phoneRaw}>{C.phoneDisplay}</a>
              <p className="small">Agendamento direto via WhatsApp ou balcão.</p>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <a className="wordmark" href="#inicio">
          ISMERIM <b>BARBEARIA</b>
        </a>
        <div>
          <p>Demonstração conceitual não oficial desenvolvida por Jarvis Digital · em revisão.</p>
          <p>Sem vínculo comercial prévio anunciado com o estabelecimento.</p>
          <details>
            <summary>Fontes e créditos das mídias</summary>
            <p>
              Conteúdo exibido por incorporações do perfil público @{C.instagramHandle.replace('@','')}, 
              com enquadramento visual técnico nesta demonstração. A disponibilidade depende do Instagram.
            </p>
            {P.map(p=>(
              <a key={p.id} href={'https://www.instagram.com/'+p.kind+'/'+p.id+'/'} target="_blank" rel="noreferrer">
                {p.credit} ↗
              </a>
            ))}
          </details>
        </div>
        <a className="social-link" href={C.instagramUrl} target="_blank" rel="noreferrer">
          Instagram <ArrowUpRight size={14}/>
        </a>
      </footer>
    </>
  );
}