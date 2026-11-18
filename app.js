// Salon's WhatsApp number, international format without "+".
const WA_NUMBER = "995000000000"; // placeholder: replace with the real salon number
const OPEN = 10 * 60, CLOSE = 21 * 60, STEP = 30; // minutes from midnight

const MASTERS = [
  {id:"nino", cat:"women", color:"#b08a57", ka:["ნინო","კოლორისტი","შეღებვა, ბალაიაჟი, რთული ტონები"], en:["Nino","Colourist","Colour, balayage, tricky tones"]},
  {id:"ana", cat:"women", color:"#8c6f8a", ka:["ანა","სტილისტი","შეჭრა და საღამოს ვარცხნილობები"], en:["Ana","Stylist","Cuts and evening updos"]},
  {id:"giorgi", cat:"men", color:"#4c5b52", ka:["გიორგი","ბარბერი","ფეიდი და კლასიკური შეჭრა"], en:["Giorgi","Barber","Fades and classic cuts"]},
  {id:"levani", cat:"men", color:"#5a4a3f", ka:["ლევანი","ბარბერი","წვერი და ცხელი პირსახოცით პარსვა"], en:["Levani","Barber","Beards and hot towel shaves"]},
];

const SERVICES = [
  {id:"w_cut", cat:"women", price:45, mins:60, ka:["ქალის შეჭრა","დაბანა, შეჭრა და ვარცხნილობა"], en:["Women's haircut","Wash, cut and blow-dry"]},
  {id:"w_blow", cat:"women", price:35, mins:45, ka:["ვარცხნილობა","დაბანა და ფენით დაყენება"], en:["Blow-dry & styling","Wash and blow-dry"]},
  {id:"w_evening", cat:"women", price:70, mins:90, ka:["საღამოს ვარცხნილობა","ღონისძიებისთვის ან ქორწილისთვის"], en:["Evening updo","For events and weddings"]},
  {id:"w_color", cat:"women", price:120, from:true, mins:120, ka:["თმის შეღებვა","ერთ ტონში, ფასი თმის სიგრძეზეა დამოკიდებული"], en:["Colouring","Single tone, price depends on length"]},
  {id:"w_balayage", cat:"women", price:220, from:true, mins:180, ka:["ბალაიაჟი / მელირება","ბუნებრივი გადასვლა და სიკაშკაშე"], en:["Balayage & highlights","Soft, natural-looking blend"]},
  {id:"w_keratin", cat:"women", price:150, from:true, mins:150, ka:["კერატინი","გლუვი და ბზინვარე თმა 3–4 თვე"], en:["Keratin treatment","Smooth, glossy hair for 3–4 months"]},
  {id:"w_care", cat:"women", price:50, mins:40, ka:["თმის მოვლა","აღმდგენი ნიღაბი და მასაჟი"], en:["Hair treatment","Repair mask and scalp massage"]},
  {id:"m_cut", cat:"men", price:30, mins:40, ka:["კაცის შეჭრა","მაკრატლით ან მანქანით, დაბანით"], en:["Men's haircut","Scissors or clippers, with wash"]},
  {id:"m_fade", cat:"men", price:35, mins:45, ka:["ფეიდი","Skin fade, სუფთა გადასვლით"], en:["Skin fade","Clean, sharp fade"]},
  {id:"m_beard", cat:"men", price:20, mins:20, ka:["წვერის მოწესრიგება","ფორმა, კონტური და ზეთი"], en:["Beard trim","Shape, line-up and oil"]},
  {id:"m_combo", cat:"men", price:45, mins:60, ka:["შეჭრა + წვერი","ყველაზე პოპულარული"], en:["Haircut + beard","Our most popular"]},
  {id:"m_shave", cat:"men", price:30, mins:30, ka:["კლასიკური პარსვა","ცხელი პირსახოცით და სამართებლით"], en:["Hot towel shave","Hot towel and straight razor"]},
  {id:"m_kids", cat:"men", price:20, mins:30, ka:["ბავშვის შეჭრა","12 წლამდე"], en:["Kids' haircut","Up to age 12"]},
];

const T = {
  en:{
    nav_services:"Services",nav_team:"Team",nav_gallery:"Work",nav_contact:"Contact",nav_book:"Book",
    hero_eyebrow:"Salon · Barbershop · Tbilisi",hero_title:"Your style, on your time",
    hero_lead:"A women's salon and a barbershop under one roof. Pick a service, a master and a time: booking takes a minute.",
    hero_cta:"Book online",hero_cta2:"Prices",
    st1:"every day",st2:"masters",st3:"online booking",st4_b:"Free",st4:"coffee & consultation",
    sv_eyebrow:"Prices",sv_title:"Services",tab_women:"Women",tab_men:"Men · Barber",
    bk_eyebrow:"Online booking",bk_title:"Book in 4 steps",
    bk_lead:"Choose and send. Your booking goes straight to the salon's WhatsApp and our admin confirms it.",
    bk_service:"Service",bk_master:"Master",bk_date:"Date",bk_time:"Time",bk_name:"Your name",bk_send:"Book on WhatsApp",
    tm_eyebrow:"Team",tm_title:"Our masters",gl_eyebrow:"Our work",gl_title:"Space & style",
    ct_title:"Visit us",ct_addr_l:"Address",ct_addr:"Saburtalo, Tbilisi",ct_hours_l:"Opening hours",ct_hours:"Every day 10:00–21:00",ct_wa:"Message us",
    foot:"Demo website. Made by Luka.",
    any:"Any free master",book:"Book",bookWith:"Book with",from:"from",min:"min",
    g_women:"Women",g_men:"Men · Barber",noSlots:"No free times left today. Pick another date.",
    e_service:"Choose a service.",e_time:"Choose a time.",e_name:"Write your name.",
    m_hi:"Hello Mane! I'd like to book:",m_service:"Service",m_master:"Master",m_when:"Date",m_name:"Name",
    m_hello:"Hello Mane!",
  },
  ka:{
    any:"ნებისმიერი თავისუფალი",book:"ჩაწერა",bookWith:"ჩაწერა:",from:"",min:"წთ",
    g_women:"ქალი",g_men:"კაცი · ბარბერი",noSlots:"დღეს თავისუფალი დრო აღარ არის. აირჩიე სხვა დღე.",
    e_service:"აირჩიე მომსახურება.",e_time:"აირჩიე დრო.",e_name:"დაწერე შენი სახელი.",
    m_hi:"გამარჯობა, Mane! მინდა ჩაწერა:",m_service:"მომსახურება",m_master:"ოსტატი",m_when:"თარიღი",m_name:"სახელი",
    m_hello:"გამარჯობა, Mane!",
  },
};

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
let lang = "ka", cat = "women";
try { lang = localStorage.getItem("mane-lang") || "ka"; } catch {}
$$("[data-i18n]").forEach(el => T.ka[el.dataset.i18n] ??= el.textContent);
const t = k => T[lang][k] ?? T.ka[k];
const wa = text => `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(text)}`;
const price = s => lang === "ka" ? `${s.price}${s.from ? "+" : ""} ₾` : `${s.from ? t("from") + " " : ""}${s.price} ₾`;
const hhmm = m => `${String(m / 60 | 0).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
const svc = () => SERVICES.find(s => s.id === $("#bService").value);

function renderMenu() {
  $("#menu").innerHTML = SERVICES.filter(s => s.cat === cat).map(s => `<li>
    <h3>${s[lang][0]}</h3><span class="pr">${price(s)}</span>
    <p>${s[lang][1]} · ${s.mins} ${t("min")}</p><button type="button" data-book="${s.id}">${t("book")}</button></li>`).join("");
  $("#svcImg").src = cat === "women" ? "img/curler.jpg" : "img/razor.jpg";
}

function renderServiceSelect() {
  const keep = $("#bService").value;
  const group = c => `<optgroup label="${t("g_" + c)}">${SERVICES.filter(s => s.cat === c)
    .map(s => `<option value="${s.id}">${s[lang][0]} · ${price(s)}</option>`).join("")}</optgroup>`;
  $("#bService").innerHTML = group("women") + group("men");
  if (keep) $("#bService").value = keep;
}

function renderMasters() {
  const s = svc(), keep = $("#bMasters input:checked")?.value || "any";
  const list = MASTERS.filter(m => m.cat === s.cat);
  $("#bMasters").innerHTML = [{id:"any"}, ...list].map(m =>
    `<label><input type="radio" name="master" value="${m.id}" ${m.id === keep ? "checked" : ""}>${m.id === "any" ? t("any") : m[lang][0]}</label>`).join("");
  if (!$("#bMasters input:checked")) $("#bMasters input").checked = true;
}

function renderSlots() {
  const s = svc(), keep = $("#bSlots input:checked")?.value, d = $("#bDate").value;
  const now = new Date(), today = now.toLocaleDateString("en-CA");
  const earliest = d === today ? now.getHours() * 60 + now.getMinutes() + 30 : 0;
  const slots = [];
  for (let m = OPEN; m + s.mins <= CLOSE; m += STEP) slots.push(m);
  const open = slots.filter(m => m >= earliest);
  $("#bSlots").innerHTML = open.length ? slots.map(m =>
    `<label><input type="radio" name="slot" value="${hhmm(m)}" ${m < earliest ? "disabled" : ""} ${hhmm(m) === keep && m >= earliest ? "checked" : ""}>${hhmm(m)}</label>`).join("")
    : `<p class="none">${t("noSlots")}</p>`;
}

function summary() {
  const s = svc(), slot = $("#bSlots input:checked")?.value, mId = $("#bMasters input:checked")?.value;
  const m = MASTERS.find(x => x.id === mId);
  $("#bSum").textContent = slot ? `${s[lang][0]} · ${m ? m[lang][0] : t("any")} · ${$("#bDate").value} ${slot} · ${price(s)}` : "";
}

function renderTeam() {
  $("#teamGrid").innerHTML = MASTERS.map(m => `<div class="member">
    <div class="avatar" style="background:${m.color}" aria-hidden="true">${m[lang][0][0]}</div>
    <h3>${m[lang][0]}</h3><p class="role">${m[lang][1]}</p><p>${m[lang][2]}</p>
    <button type="button" data-master="${m.id}">${t("bookWith")} ${m[lang][0]}</button></div>`).join("");
}

function applyLang() {
  document.documentElement.lang = lang;
  $$("[data-i18n]").forEach(el => el.textContent = t(el.dataset.i18n));
  $("#lang").textContent = lang === "ka" ? "EN" : "ქარ";
  renderMenu(); renderServiceSelect(); renderMasters(); renderSlots(); renderTeam(); summary();
  $("#waFloat").href = $("#waText").href = wa(t("m_hello"));
}

$("#lang").onclick = () => {
  lang = lang === "ka" ? "en" : "ka";
  try { localStorage.setItem("mane-lang", lang); } catch {}
  applyLang();
};

$("#tabs").onclick = e => {
  const b = e.target.closest(".tab"); if (!b) return;
  cat = b.dataset.cat;
  $$(".tab").forEach(x => { x.classList.toggle("on", x === b); x.setAttribute("aria-selected", x === b); });
  renderMenu();
};

function pickService(id) {
  $("#bService").value = id;
  renderMasters(); renderSlots(); summary();
  $("#book").scrollIntoView();
}
$("#menu").onclick = e => { const b = e.target.closest("[data-book]"); if (b) pickService(b.dataset.book); };
$("#teamGrid").onclick = e => {
  const b = e.target.closest("[data-master]"); if (!b) return;
  const m = MASTERS.find(x => x.id === b.dataset.master);
  if (svc().cat !== m.cat) $("#bService").value = SERVICES.find(s => s.cat === m.cat).id;
  renderMasters();
  $(`#bMasters input[value=${m.id}]`).checked = true;
  renderSlots(); summary();
  $("#book").scrollIntoView();
};

$("#bService").onchange = () => { renderMasters(); renderSlots(); summary(); };
$("#bDate").onchange = () => { renderSlots(); summary(); };
$("#bMasters").onchange = summary;
$("#bSlots").onchange = summary;

$("#bookForm").onsubmit = e => {
  e.preventDefault();
  const s = svc(), slot = $("#bSlots input:checked")?.value, name = $("#bName").value.trim();
  const err = !s ? "e_service" : !slot ? "e_time" : !name ? "e_name" : "";
  $("#bErr").textContent = err ? t(err) : "";
  if (err) return;
  const m = MASTERS.find(x => x.id === $("#bMasters input:checked").value);
  const msg = [t("m_hi"),
    `${t("m_service")}: ${s[lang][0]} (${price(s)}, ~${s.mins} ${t("min")})`,
    `${t("m_master")}: ${m ? m[lang][0] : t("any")}`,
    `${t("m_when")}: ${$("#bDate").value}, ${slot}`,
    `${t("m_name")}: ${name}`].join("\n");
  window.open(wa(msg), "_blank", "noopener");
};

// date limits: today .. +30 days
const d = $("#bDate"), today = new Date();
d.min = d.value = today.toLocaleDateString("en-CA");
d.max = new Date(today.getTime() + 30 * 864e5).toLocaleDateString("en-CA");
// after the last slot of the day, start the picker on tomorrow
if (today.getHours() * 60 + today.getMinutes() + 30 > CLOSE - STEP) d.value = new Date(today.getTime() + 864e5).toLocaleDateString("en-CA");

// nav: transparent over the hero, solid after scrolling
const nav = $(".nav"), burger = $("#burger"), links = $("#links");
const onScroll = () => nav.classList.toggle("scrolled", scrollY > 40);
addEventListener("scroll", onScroll, {passive:true}); onScroll();
burger.onclick = () => { const o = links.classList.toggle("open"); burger.setAttribute("aria-expanded", o); };
links.onclick = e => { if (e.target.tagName === "A") { links.classList.remove("open"); burger.setAttribute("aria-expanded", false); } };

applyLang();
