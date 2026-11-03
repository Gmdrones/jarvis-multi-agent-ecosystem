import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {ArrowUpRight,ArrowDown,Menu,X,MapPin,Play} from 'lucide-react';
import {COMPANY_DATA as C} from './data';
const posts=[
 {id:'DeUW2npkfrx',kind:'p',title:'Maquiagem & expressão',credit:'Studio 962 · maquiagem creditada a Roger Makeupart',aspect:.75,y:.23},
 {id:'DfFwV_Zv2AM',kind:'reel',title:'A cor ganha movimento.',credit:'Studio 962 · mechas creditadas a Lucas Rufiino',aspect:9/16,y:.3},
 {id:'Dd61KmhFXCc',kind:'p',title:'Beleza nos detalhes.',credit:'Studio 962 e Andreia Manicure RJ',aspect:.75,y:.35}
];
function Media({post,hero=false}:{post:typeof posts[number],hero?:boolean}){
 const ref=useRef<HTMLDivElement>(null);
 const url='https://www.instagram.com/'+post.kind+'/'+post.id+'/';
 useEffect(()=>{
  const el=ref.current;if(!el)return;
  const fit=()=>{const w=el.clientWidth,h=el.clientHeight;const mediaW=Math.max(w,h*post.aspect)*1.14;const iframeW=post.kind==='reel'?mediaW/(.5625/.8):mediaW;const mediaH=mediaW/post.aspect;
   el.style.setProperty('--iw',iframeW+'px');el.style.setProperty('--ix',(w-iframeW)/2+'px');el.style.setProperty('--iy',-(54+(mediaH-h)*post.y)+'px');el.style.setProperty('--ih',(54+mediaH+260)+'px');
   el.querySelectorAll('iframe').forEach(f=>{f.title=post.title;f.tabIndex=-1});
  };fit();const resize=new ResizeObserver(fit);resize.observe(el);const mutation=new MutationObserver(fit);mutation.observe(el,{childList:true});return()=>{resize.disconnect();mutation.disconnect()};
 },[post]);
 return <div className={'media-mask '+(hero?'hero-media':'')} ref={ref} data-media={post.id} aria-label={post.title}>
  <blockquote className="instagram-media" data-instgrm-permalink={url} data-instgrm-version="14"><a href={url} target="_blank" rel="noreferrer">Abrir {post.title}</a></blockquote>
 </div>
}
export default function App(){
 const [menu,setMenu]=useState(false);const menuButton=useRef<HTMLButtonElement>(null);const mobileNav=useRef<HTMLElement>(null);
 useLayoutEffect(()=>{if(menu)mobileNav.current?.querySelector<HTMLAnchorElement>('a')?.focus()},[menu]);
 useEffect(()=>{
  const close=(e:KeyboardEvent)=>{if(e.key==='Escape'&&document.getElementById('mobile-nav')){setMenu(false);menuButton.current?.focus()}};window.addEventListener('keydown',close);
  const script=document.createElement('script');script.src='https://www.instagram.com/embed.js';script.async=true;document.body.appendChild(script);
  return()=>{window.removeEventListener('keydown',close);script.remove()};
 },[]);
 return <>
 <a className="skip" href="#conteudo">Pular para o conteúdo</a>
 <div className="demo-bar">Demonstração não oficial · em revisão <span>Jarvis Digital</span></div>
 <header><a className="wordmark" href="#inicio">STUDIO <b>962</b><small>ESPLANADA DA BARRA</small></a><nav className="desktop-nav" aria-label="Navegação principal"><a href="#trabalhos">O nosso olhar</a><a href="#servicos">Serviços</a><a href="#contato">Encontre-nos</a></nav><a className="header-contact" href={C.whatsappUrl} target="_blank" rel="noreferrer">Agende seu momento <ArrowUpRight size={16}/></a><button ref={menuButton} className="menu-toggle" aria-label={menu?'Fechar menu':'Abrir menu'} aria-expanded={menu} aria-controls="mobile-nav" onClick={()=>setMenu(!menu)}>{menu?<X/>:<Menu/>}</button></header>
 {menu&&<nav ref={mobileNav} id="mobile-nav" className="mobile-nav" aria-label="Navegação móvel">{[['O nosso olhar','#trabalhos'],['Serviços','#servicos'],['Encontre-nos','#contato']].map(([text,href])=><a href={href} key={href} onClick={()=>setMenu(false)}>{text}<ArrowUpRight/></a>)}</nav>}
 <main id="conteudo">
  <section id="inicio" className="hero">
   <div className="hero-visual"><Media post={posts[0]} hero/></div><div className="hero-wash"/>
   <div className="hero-content"><p className="eyebrow">STUDIO 962 · BARRA DA TIJUCA</p><h1>A beleza<br/>é ser <em>você.</em></h1><p className="hero-intro">Cabelo, cor e expressão.<br/>Seu momento, na Esplanada da Barra.</p><a className="button" href={C.whatsappUrl} target="_blank" rel="noreferrer">Agende seu momento <ArrowUpRight size={18}/></a></div>
   <div className="hero-bottom"><span>CORTE · COR · MEGA HAIR</span><a href="#trabalhos">EXPLORE O STUDIO <ArrowDown size={16}/></a></div>
  </section>
  <section id="trabalhos" className="gallery section-pad">
   <div className="section-label"><span>01 — O NOSSO OLHAR</span><span>STUDIO 962 / RIO DE JANEIRO</span></div>
   <div className="gallery-heading"><h2>De perto,<br/><em>cada detalhe.</em></h2><p>Cor, textura e movimento.<br/>Conheça trabalhos publicados pelo Studio.</p></div>
   <div className="gallery-grid"><article className="work work-video"><div className="media-container"><Media post={posts[1]}/><div className="video-hint"><Play size={12} fill="currentColor"/> TOQUE PARA ASSISTIR</div></div><div className="work-label"><h3>{posts[1].title}</h3><span>01 / FILME</span></div><a className="accessible-original" href={'https://www.instagram.com/reel/'+posts[1].id+'/'} target="_blank" rel="noreferrer">Abrir vídeo original <ArrowUpRight size={13}/></a></article>
    <article className="work work-photo"><Media post={posts[2]}/><div className="work-label"><h3>{posts[2].title}</h3><span>02 / NAILS</span></div></article></div>
  </section>
  <section id="servicos" className="services section-pad"><div className="section-label"><span>02 — SEU MOMENTO</span><span>BELEZA & EXPRESSÃO</span></div><div className="services-grid"><div><p className="eyebrow">DO SEU JEITO</p><h2>Encontre sua<br/><em>assinatura.</em></h2><p className="section-copy">Escolha por onde começar.<br/>Nossa conversa começa com você.</p></div><div className="service-rows">{['Corte & coloração','Mega hair','Manicure','Barbearia'].map((s,i)=><a href={C.whatsappUrl} target="_blank" rel="noreferrer" key={s}><span>0{i+1}</span><h3>{s}</h3><ArrowUpRight size={22}/></a>)}</div></div></section>
  <section id="contato" className="contact section-pad"><div className="section-label"><span>03 — ENCONTRE-NOS</span><span>ESPLANADA DA BARRA</span></div><div className="contact-grid"><div><p className="eyebrow">BARRA DA TIJUCA</p><h2>O próximo<br/><em>momento é seu.</em></h2><a className="button dark" href={C.whatsappUrl} target="_blank" rel="noreferrer">Converse com o Studio <ArrowUpRight size={18}/></a></div><div className="address"><MapPin size={26} strokeWidth={1}/><h3>Studio 962</h3><p>{C.address}<br/>Barra da Tijuca · Rio de Janeiro, RJ<br/>CEP 22631-003</p><a className="text-link" href={C.mapsUrl} target="_blank" rel="noreferrer">Como chegar <ArrowUpRight size={15}/></a><a className="phone" href={'tel:+'+C.phoneRaw}>{C.phoneDisplay}</a><p className="small">Valores e disponibilidade: consulte a equipe.</p></div></div></section>
 </main>
 <footer><a className="wordmark" href="#inicio">STUDIO <b>962</b></a><div><p>Demonstração não oficial por Jarvis Digital · em revisão.</p><p>Sem vínculo comercial anunciado com o estabelecimento.</p><details><summary>Fontes e créditos das mídias</summary><p>Conteúdo exibido por incorporações do perfil público, com enquadramento visual nesta demonstração. A disponibilidade depende do Instagram.</p>{posts.map(p=><a key={p.id} href={'https://www.instagram.com/'+p.kind+'/'+p.id+'/'} target="_blank" rel="noreferrer">{p.credit} ↗</a>)}</details></div><a className="social-link" href={C.instagramUrl} target="_blank" rel="noreferrer">Instagram <ArrowUpRight size={14}/></a></footer>
 </>;
}