import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {s} from '../theme';
import {
	BigText,
	ChapterCard,
	Credit,
	DarkBg,
	LowerThird,
	PhotoShot,
	StatusBadge,
	VideoShot,
} from '../components/Primitives';
import {
	AgeGap,
	Chips,
	Counter,
	DateCard,
	DocCard,
	DocImage,
	Legend,
	NameCards,
	QuestionMarks,
	SplitScreen,
	Timeline,
} from '../components/Cards';

/**
 * Storyboard. Every scene starts/ends on the original audio timestamps (seconds).
 * `media` and `credit` feed the sources CSV and the on-screen attribution.
 * Times inside a scene (e.g. `at`) are frames relative to the scene start.
 */
export type Scene = {
	from: number;
	to: number;
	id: string;
	desc: string; // what is said
	visual: string; // what is shown
	media: string[]; // files in public/media
	sfx?: 'whoosh' | 'impact';
	render: () => React.ReactNode;
};

const KREMLIN = 'Foto: Kremlin.ru · CC BY 4.0';
const KREMLIN_V = 'Video: Kremlin.ru · CC BY 4.0';
const rel = (abs: number, sceneFrom: number) => s(abs - sceneFrom);

export const SCENES: Scene[] = [
	/* ------------------------------ HOOK ------------------------------ */
	{
		from: 0, to: 3.5, id: 'hook-1', desc: 'Dunyodagi eng qudratli siyosatchilardan biri.',
		visual: 'Putin sahnaga chiqmoqda — «Yil yakunlari 2025» (Kremlin.ru video)', media: ['v_presser_walk.mp4'],
		render: () => (<><VideoShot src="v_presser_walk.mp4" startFrom={3.4} zoom={[1.12, 1.2]} origin="55% 45%" /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 3.5, to: 7.1, id: 'hook-2', desc: 'Uning qarorlari millionlab insonlarning hayotiga ta’sir qiladi.',
		visual: 'Putin minbarda, 9-may 2026 (Kremlin.ru video)', media: ['v_may9_podium2.mp4'],
		render: () => (<><VideoShot src="v_may9_podium2.mp4" startFrom={0.5} zoom={[1.0, 1.12]} origin="50% 35%" /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 7.1, to: 13.2, id: 'hook-3', desc: 'Uchrashuvlari, nutqlari… xalqaro yangilikka aylanadi.',
		visual: 'Matbuot anjumani zali, jurnalistlar (umumiy plan) — Kremlin.ru', media: ['v_presser_hall.mp4'],
		render: () => (<><VideoShot src="v_presser_hall.mp4" startFrom={0} zoom={[1.0, 1.1]} /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 13.2, to: 19.5, id: 'kremlin', desc: 'Kreml juda kam gapiradigan soha bor.',
		visual: 'Moskva Kremli ichki zali, davlat mukofotlari marosimi (Kremlin.ru video)', media: ['v_awards_hall.mp4'], sfx: 'whoosh',
		render: () => (
			<>
				<VideoShot src="v_awards_hall.mp4" startFrom={0} zoom={[1.0, 1.1]} dim={0.2} />
				<LowerThird name="Moskva Kremli" role="Rossiya prezidenti qarorgohi" delay={10} />
				<Credit text={KREMLIN_V} />
			</>
		),
	},
	{
		from: 19.5, to: 22.2, id: 'private', desc: 'Bu — uning shaxsiy hayoti.',
		visual: 'Sarlavha «SHAXSIY HAYOT» xira video ustida', media: ['v_presser_close.mp4'], sfx: 'impact',
		render: () => (<><VideoShot src="v_presser_close.mp4" startFrom={2} blur={14} dim={0.6} /><BigText title="SHAXSIY HAYOT" size={150} /></>),
	},
	{
		from: 22.2, to: 23.7, id: 'q-who', desc: 'Putin kim bilan yashaydi?',
		visual: 'Kreml tarqatgan oilaviy surat (2002), oila a’zolarining yuzi ataylab ko‘rsatilmagan', media: ['family2002_1.jpg'],
		render: () => (<><PhotoShot src="family2002_1.jpg" dim={0.25} /><Credit text={KREMLIN} /></>),
	},
	{
		from: 23.7, to: 28.5, id: 'q-lyudmila', desc: 'Sobiq rafiqasi bilan ajrashgani…',
		visual: 'Lyudmila Putina — Kreml arxivi surati (1988)', media: ['lyudmila_1988.jpg'],
		render: () => (
			<>
				<PhotoShot src="lyudmila_1988.jpg" frame from={{x: 0, y: 10, s: 1}} to={{x: 0, y: -10, s: 1.06}} />
				<LowerThird name="Lyudmila Putina" role="Sobiq rafiqasi · 1983–2013" />
				<Credit text={KREMLIN} />
			</>
		),
	},
	{
		from: 28.5, to: 36.4, id: 'q-kabaeva', desc: 'Alina Kabayeva nega doim uning ismi bilan tilga olinadi?',
		visual: 'Putin Alina Kabayevaga orden topshirmoqda, 21.12.2005 (Kremlin.ru)', media: ['kabaeva_2005.jpg'],
		render: () => (
			<>
				<PhotoShot src="kabaeva_2005.jpg" frame from={{x: 0, y: 0, s: 1}} to={{x: -30, y: 0, s: 1.1}} />
				<LowerThird name="Alina Kabayeva" role="Olimpiya chempioni · badiiy gimnastika" delay={30} />
				<Credit text={KREMLIN + ' · 21.12.2005'} />
			</>
		),
	},
	{
		from: 36.4, to: 42.4, id: 'q-children', desc: 'Yashirin farzandlar haqida jurnalistlar nimani aniqlagan?',
		visual: 'Tipografik karta — surat ishlatilmaydi (voyaga yetmaganlar)', media: [],
		render: () => (<><QuestionMarks /><BigText title="Yashirin farzandlar?" sub="Jurnalistik surishtiruvlar nimani aniqlagan?" /></>),
	},
	/* ------------------------------ TITLE ------------------------------ */
	{
		from: 42.4, to: 54.0, id: 'title', desc: 'Bugun biz… gaplashamiz.',
		visual: 'Asosiy sarlavha; fon — Kreml zali (Kremlin.ru video)', media: ['v_awards_hall.mp4'], sfx: 'impact',
		render: () => (
			<>
				<VideoShot src="v_awards_hall.mp4" startFrom={0} blur={6} dim={0.62} zoom={[1.05, 1.12]} />
				<BigText kicker="HUJJATLI FILM" title="Kreml sukut saqlaydigan savollar" sub="Vladimir Putinning shaxsiy hayoti: faktlar, surishtiruvlar va tasdiqlanmagan da’volar" size={112} />
			</>
		),
	},
	{
		from: 54.0, to: 71.2, id: 'legend', desc: 'Rasmiy faktlar, tekshirilgan materiallar, tasdiqlanmagan da’volar.',
		visual: 'Uch darajali «haqiqat» legendasi; keyin xulosa iborasi', media: [],
		render: () => (
			<>
				<Sequence durationInFrames={s(10.6)}>
					<Legend times={[2, rel(56.5, 54), rel(58.6, 54)]} />
				</Sequence>
				<Sequence from={s(10.6)}>
					<DarkBg />
					<BigText title="Eng katta sir — nimani aniq bilmasligimizda" size={86} />
				</Sequence>
			</>
		),
	},
	/* ------------------------------ CHAPTER 1 ------------------------------ */
	{
		from: 71.2, to: 75.6, id: 'ch1', desc: 'Birinchi sir: Putinning rasmiy oilasi.',
		visual: 'Bob kartasi', media: ['wedding2.jpg'], sfx: 'whoosh',
		render: () => <ChapterCard n="1" title="Putinning rasmiy oilasi" bg={<PhotoShot src="wedding2.jpg" />} />,
	},
	{
		from: 75.6, to: 80.3, id: 'wedding', desc: '1983-yilda Lyudmila Shkrebnevaga uylangan.',
		visual: 'To‘y surati 28.07.1983 — Kreml arxivi', media: ['wedding2.jpg'],
		render: () => (
			<>
				<PhotoShot src="wedding2.jpg" frame from={{x: 0, y: 30, s: 1}} to={{x: 0, y: -20, s: 1.08}} />
				<LowerThird name="1983" role="Vladimir Putin va Lyudmila Shkrebneva · to‘y kuni" status="fact" />
				<Credit text={KREMLIN + ' · Putinning shaxsiy arxivi'} />
			</>
		),
	},
	{
		from: 80.3, to: 87.7, id: 'kgb', desc: 'Sovet davlat xavfsizlik tizimida ishlayotgan yosh xodim edi.',
		visual: 'Putin KGB formasida — xodim shaxsiy ishidagi surat (~1980)', media: ['kgb.jpg'],
		render: () => (
			<>
				<PhotoShot src="kgb.jpg" frame from={{x: 0, y: 40, s: 1.0}} to={{x: 0, y: -10, s: 1.12}} />
				<LowerThird name="KGB" role="Sovet davlat xavfsizlik qo‘mitasi · 1975–1991" delay={s(3.3)} />
				<Credit text={KREMLIN + ' · KGB shaxsiy ishidagi surat'} />
			</>
		),
	},
	{
		from: 87.7, to: 92.4, id: 'daughters-born', desc: 'Ikki qiz tug‘ildi: Mariya va Yekaterina.',
		visual: 'Ism kartalari: Mariya (1985), Yekaterina (1986)', media: [],
		render: () => (
			<NameCards status="fact" names={[{name: 'Mariya', sub: '1985-yilda tug‘ilgan', at: rel(89.9, 87.7)}, {name: 'Yekaterina', sub: '1986-yilda tug‘ilgan', at: rel(90.7, 87.7)}]} />
		),
	},
	{
		from: 92.4, to: 96.1, id: 'president', desc: 'Putin Rossiyaning eng yuqori lavozimiga ko‘tarildi.',
		visual: 'Putin Kremldagi marosimda minbarda (Kremlin.ru video)', media: ['v_awards_podium.mp4'],
		render: () => (<><VideoShot src="v_awards_podium.mp4" startFrom={0.5} zoom={[1.0, 1.1]} origin="50% 30%" /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 96.1, to: 101.0, id: 'family-hidden', desc: 'Oilasi OAVdan tobora uzoqlashdi.',
		visual: 'Kreml tarqatgan 2002-yilgi oilaviy surat: yuzlar ataylab ko‘rsatilmagan', media: ['family2002_1.jpg'],
		render: () => (
			<>
				<PhotoShot src="family2002_1.jpg" from={{x: 0, y: 0, s: 1}} to={{x: 0, y: 0, s: 1.1}} />
				<LowerThird name="Primorye, 2002" role="Kreml tarqatgan surat: oila a’zolarining yuzi ko‘rsatilmagan" delay={12} />
				<Credit text={KREMLIN} />
			</>
		),
	},
	{
		from: 101.0, to: 107.3, id: 'events', desc: 'Ko‘plab tadbirlarda qatnashardi, farzandlari ko‘rinmasdi.',
		visual: 'Kreml marosimi, umumiy plan (Kremlin.ru video)', media: ['v_awards_wide.mp4'],
		render: () => (<><VideoShot src="v_awards_wide.mp4" startFrom={0} zoom={[1.0, 1.15]} origin="50% 45%" /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 107.3, to: 111.7, id: 'press', desc: 'Jurnalistlar va jamoatchilikda savollar tug‘dirgan.',
		visual: 'Matbuot anjumani zali, umumiy plan (Kremlin.ru video)', media: ['v_presser_close2.mp4'],
		render: () => (<><VideoShot src="v_presser_close2.mp4" startFrom={1.0} zoom={[1.05, 1.12]} /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 111.7, to: 116.4, id: '2013', desc: '2013-yil. Iyun oyida kutilmagan voqea yuz berdi.',
		visual: 'Sana kartasi', media: [], sfx: 'impact',
		render: () => <DateCard small="IYUN" big="2013" />,
	},
	{
		from: 116.4, to: 124.5, id: 'divorce', desc: 'Ajrashayotganini omma oldida ma’lum qildi.',
		visual: 'Putin va Lyudmila Putina, inauguratsiyadan keyin Sobornaya maydoni, 07.05.2012 (Kremlin.ru)', media: ['putin_lyudmila_2012.jpg'],
		render: () => (
			<>
				<PhotoShot src="putin_lyudmila_2012.jpg" frame from={{x: 0, y: 20, s: 1}} to={{x: 0, y: -10, s: 1.08}} />
				<LowerThird name="6-iyun, 2013" role="Ajrashuv birgalikda e’lon qilindi" status="fact" delay={8} />
				<div style={{position: 'absolute', right: 70, bottom: 250, fontFamily: 'sans-serif'}}><StatusBadge status="fact" delay={20} /></div>
				<Credit text={KREMLIN + ' · Surat: 7-may 2012'} />
			</>
		),
	},
	{
		from: 124.5, to: 127.1, id: '30y', desc: 'O‘ttiz yil davom etgan nikoh yakunlandi.',
		visual: '1983 → 2013 = 30 yil', media: [],
		render: () => <DateCard small="1983 — 2013" big="30 yil" sub="Nikoh yakunlandi (rasmiy ajrashuv 2014-yilda rasmiylashtirilgan)" />,
	},
	{
		from: 127.1, to: 133.4, id: 'questions', desc: 'Savollar kamaymadi, aksincha ko‘paydi.',
		visual: 'Putin yaqin plan (Kremlin.ru video)', media: ['v_presser_close.mp4'],
		render: () => (<><VideoShot src="v_presser_close.mp4" startFrom={4} zoom={[1.05, 1.18]} origin="50% 35%" /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 133.4, to: 139.9, id: 'rumours', desc: 'Taniqli sportchi bilan bog‘liq eski mish-mishlar qaytdi.',
		visual: 'Sidney-2000 Olimpiadasi podiumi: Kabayeva (chapda, bronza)', media: ['kabaeva_syd2000.jpg'],
		render: () => (
			<>
				<PhotoShot src="kabaeva_syd2000.jpg" frame from={{x: 0, y: 0, s: 1}} to={{x: 60, y: 0, s: 1.12}} />
				<Credit text="Foto: Tom Theobald · CC BY 3.0 · Sidney, 29.09.2000" />
			</>
		),
	},
	/* ------------------------------ CHAPTER 2 ------------------------------ */
	{
		from: 139.9, to: 143.6, id: 'ch2', desc: 'Ikkinchi sir: Putindan o‘ttiz yosh kichik ayol.',
		visual: 'Bob kartasi', media: ['kabaeva_2005.jpg'], sfx: 'whoosh',
		render: () => <ChapterCard n="2" title="Putindan o‘ttiz yosh kichik ayol" bg={<PhotoShot src="kabaeva_2005.jpg" fit="cover" />} />,
	},
	{
		from: 143.6, to: 148.4, id: 'kabaeva', desc: 'Alina Kabayeva. Sport muxlislariga yaxshi tanish.',
		visual: 'Kabayeva Kremlda orden olmoqda, 2005 (Kremlin.ru)', media: ['kabaeva_2005.jpg'],
		render: () => (
			<>
				<PhotoShot src="kabaeva_2005.jpg" frame from={{x: 0, y: 0, s: 1.05}} to={{x: -60, y: 0, s: 1.2}} />
				<LowerThird name="Alina Kabayeva" role="1983-yilda Toshkentda tug‘ilgan · badiiy gimnastika" delay={4} />
				<Credit text={KREMLIN + ' · 21.12.2005'} />
			</>
		),
	},
	{
		from: 148.4, to: 151.1, id: 'olympic', desc: 'Badiiy gimnastika bo‘yicha Olimpiya chempioni.',
		visual: 'Kabayeva Olimpiya podiumida, Sidney-2000', media: ['kabaeva_syd2000.jpg'],
		render: () => (
			<>
				<PhotoShot src="kabaeva_syd2000.jpg" frame from={{x: 80, y: 0, s: 1.15}} to={{x: 120, y: 0, s: 1.25}} />
				<Credit text="Foto: Tom Theobald · CC BY 3.0 · Sidney-2000" />
			</>
		),
	},
	{
		from: 151.1, to: 155.0, id: 'athens', desc: '2004-yilda Afinada oltin medal.',
		visual: 'Infografika: Afina-2004, oltin medal', media: [],
		render: () => <DateCard small="AFINA · OLIMPIYA O‘YINLARI" big="2004" sub="Badiiy gimnastika, mutlaq birinchilik — oltin medal" status="fact" />,
	},
	{
		from: 155.0, to: 159.6, id: 'career', desc: 'Sportni tark etib, siyosat va media sohasida faoliyat.',
		visual: 'Faoliyat bosqichlari', media: [],
		render: () => (
			<Chips title="Sportdan keyin" status="fact" items={[{at: 6, text: '2007–2014 · Davlat Dumasi deputati'}, {at: 40, text: '2014– · National Media Group'}]} />
		),
	},
	{
		from: 159.6, to: 163.8, id: 'press-world', desc: 'Dunyo matbuotida boshqa sabab bilan mashhur bo‘ldi.',
		visual: 'Xalqaro matbuot zali (Rossiya–Afrika anjumani, Kremlin.ru video)', media: ['v_africa_wide2.mp4'],
		render: () => (<><VideoShot src="v_africa_wide2.mp4" startFrom={0} zoom={[1.0, 1.1]} /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 163.8, to: 169.6, id: 'companion', desc: 'Kabayeva Putinning ehtimoliy yaqin hamrohi sifatida tilga olinadi.',
		visual: 'Split: Putin (video) | Kabayeva (2005 surat); TASDIQLANMAGAN belgisi', media: ['v_may9_podium3.mp4', 'kabaeva_2005.jpg'],
		render: () => (
			<>
				<SplitScreen
					left={<VideoShot src="v_may9_podium3.mp4" startFrom={0} zoom={[1.15, 1.2]} origin="50% 30%" />}
					right={<PhotoShot src="kabaeva_2005.jpg" fit="cover" from={{x: 0, y: 0, s: 1.6}} to={{x: -40, y: 0, s: 1.7}} />}
					leftLabel="PUTIN"
					rightLabel="KABAYEVA"
					rightAt={6}
				/>
				<div style={{position: 'absolute', width: '100%', bottom: 260, textAlign: 'center'}}><StatusBadge status="unconfirmed" delay={30} label="«EHTIMOLIY HAMROH» — TASDIQLANMAGAN" /></div>
				<Credit text={KREMLIN} />
			</>
		),
	},
	{
		from: 169.6, to: 173.6, id: 'age', desc: 'Yosh farqi qariyb o‘ttiz yil.',
		visual: 'Infografika: 1952 — 1983', media: [],
		render: () => <AgeGap />,
	},
	{
		from: 173.6, to: 181.6, id: '2008-paper', desc: '2008-yilda bir gazeta… yozdi. Katta shov-shuv.',
		visual: 'Hujjat kartasi: «Moskovskiy korrespondent», aprel 2008', media: [],
		render: () => (
			<DocCard outlet="«MOSKOVSKIY KORRESPONDENT» GAZETASI" date="Aprel, 2008" headline="Putin Lyudmila bilan ajrashib, Kabayevaga uylanmoqchi — gazeta da’vosi" status="unconfirmed" lines={[{at: rel(179.5, 173.6), text: 'Xabar katta shov-shuvga sabab bo‘ldi; gazeta tez orada yopildi.'}]} />
		),
	},
	{
		from: 181.6, to: 187.8, id: '2008-denial', desc: 'Putin rad etdi. Kabayeva ham inkor qilgan.',
		visual: 'Kreml stenogrammasidan iqtibos, 18.04.2008, Sardiniya', media: [],
		render: () => (
			<DocCard
				outlet="KREMLIN.RU · STENOGRAMMA"
				date="18-aprel, 2008 · Sardiniya"
				headline="Putin xabarni rad etdi"
				status="fact"
				quote={{text: 'В том, что Вы сказали, нет ни одного слова правды', translation: '«Siz aytgan gaplarda bir og‘iz ham haqiqat yo‘q»', who: 'Vladimir Putin, Silvio Berluskoni bilan matbuot anjumanida'}}
				lines={[{at: rel(183.6, 181.6), text: 'Kabayeva ham romantik munosabatni inkor qilgan.'}]}
			/>
		),
	},
	{
		from: 187.8, to: 192.4, id: 'debate', desc: 'Xalqaro matbuotda yillar davomida muhokama qilindi.',
		visual: 'Matbuot anjumani zali (Kremlin.ru video)', media: ['v_africa_wide.mp4'],
		render: () => (<><VideoShot src="v_africa_wide.mp4" startFrom={0.6} zoom={[1.0, 1.1]} /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 192.4, to: 203.7, id: 'nmg', desc: 'National Media Group rahbariyatida faoliyat yuritdi.',
		visual: 'Ma’lumot kartasi: NMG direktorlar kengashi raisi (2014-yildan)', media: ['kabaeva_2005.jpg'],
		render: () => (
			<DocCard
				outlet="NATIONAL MEDIA GROUP"
				date="2014-yildan"
				headline="Alina Kabayeva — direktorlar kengashi raisi"
				status="fact"
				lines={[{at: rel(198.7, 192.4), text: 'Rossiyaning eng yirik xususiy media xoldinglaridan biri: telekanallar, gazetalar, radio.'}]}
				bg={<PhotoShot src="kabaeva_2005.jpg" fit="cover" />}
			/>
		),
	},
	{
		from: 203.7, to: 210.5, id: 'bridge', desc: 'Eng katta shov-shuv farzandlari haqidagi xabarlar bilan bog‘liq.',
		visual: 'Tipografik o‘tish', media: [],
		render: () => (<><QuestionMarks /><BigText title="Farzandlar haqidagi xabarlar" /></>),
	},
	/* ------------------------------ CHAPTER 3 ------------------------------ */
	{
		from: 210.5, to: 213.4, id: 'ch3', desc: 'Uchinchi sir: yashirin o‘g‘illar bormi?',
		visual: 'Bob kartasi', media: [], sfx: 'whoosh',
		render: () => <ChapterCard n="3" title="Putinning yashirin o‘g‘illari bormi?" />,
	},
	{
		from: 213.4, to: 220.2, id: 'dossier', desc: '2024-yil sentyabr — Dossier Center.',
		visual: 'Hujjat kartasi: Dossier Center, 04.09.2024', media: [],
		render: () => (
			<DocCard outlet="DOSSIER CENTER" date="4-sentabr, 2024" headline="Jurnalistik surishtiruv: Putin va Kabayevaning ehtimoliy farzandlari" status="investigation" lines={[{at: 60, text: 'Mustaqil surishtiruv tashkiloti (London)'}]} />
		),
	},
	{
		from: 220.2, to: 229.4, id: 'sons', desc: 'Ikki o‘g‘il borligi taxmin qilinadi: Ivan va Vladimir.',
		visual: 'Ism kartalari — fotosurat yo‘q (voyaga yetmaganlar, maxfiylik)', media: [],
		render: () => (
			<NameCards status="unconfirmed" title="Surishtiruvga ko‘ra: ikki o‘g‘il" caption="Surishtiruvda keltirilgan ismlar · Kreml tasdiqlamagan" names={[{name: 'Ivan', at: rel(225.7, 220.2)}, {name: 'Vladimir', at: rel(226.9, 220.2)}]} />
		),
	},
	{
		from: 229.4, to: 238.2, id: 'residence', desc: 'Qo‘riqlanadigan qarorgohlar, maxsus o‘qituvchilar.',
		visual: 'Chips: surishtiruv da’volari', media: [],
		render: () => (
			<Chips status="investigation" title="Dossier Center da’volari" items={[{at: 10, text: 'Qattiq qo‘riqlanadigan qarorgohlar'}, {at: rel(233.6, 229.4), text: 'Maxsus o‘qituvchilar'}, {at: rel(235.2, 229.4), text: 'Tarbiyachilar'}]} />
		),
	},
	{
		from: 238.2, to: 255.2, id: 'systema', desc: '2026-yil may — RFE/RL «Sistema» surishtiruvi.',
		visual: 'Hujjat kartasi: Systema (RFE/RL), 28.05.2026', media: [],
		render: () => (
			<DocCard
				outlet="RFE/RL · «SISTEMA»"
				date="28-may, 2026"
				headline="Bolalarga dars bergan xorijlik mutaxassislar va hujjatlar o‘rganildi"
				status="investigation"
				lines={[
					{at: rel(244.3, 238.2), text: 'Xorijlik o‘qituvchilar va ularning ishiga oid hujjatlar tahlil qilingan'},
					{at: rel(250.5, 238.2), text: 'Ingliz va nemis tillari uchun xorijlik tarbiyachilar jalb qilingan'},
				]}
			/>
		),
	},
	{
		from: 255.2, to: 269.2, id: 'disclaimer', desc: 'Putin tasdiqlamagan. Rasmiy fakt emas — da’volar.',
		visual: 'Ogohlantirish kartasi', media: [], sfx: 'impact',
		render: () => (
			<>
				<DarkBg />
				<BigText kicker="MUHIM" title="Putin bu bolalarni o‘z farzandlari deb omma oldida tasdiqlamagan" size={74} />
				<div style={{position: 'absolute', width: '100%', bottom: 280, textAlign: 'center'}}>
					<StatusBadge status="unconfirmed" delay={rel(262.2, 255.2)} label="RASMIY FAKT EMAS — SURISHTIRUV DA’VOSI" />
				</div>
			</>
		),
	},
	{
		from: 269.2, to: 275.9, id: 'secrecy', desc: 'Nega bunchalik katta maxfiylik?',
		visual: 'Kreml zali, xira fon (Kremlin.ru video) + savol', media: ['v_awards_wide.mp4'],
		render: () => (
			<>
				<VideoShot src="v_awards_wide.mp4" startFrom={2} blur={8} dim={0.6} zoom={[1.1, 1.2]} />
				<BigText title="Nega bunchalik maxfiylik?" size={96} />
			</>
		),
	},
	{
		from: 275.9, to: 284.2, id: 'reasons', desc: 'Xavfsizlik, shaxsiy daxlsizlik, siyosiy imij.',
		visual: 'Chips + «faqat taxmin»', media: [],
		render: () => (
			<Chips title="Ehtimoliy sabablar" items={[{at: 8, text: 'Xavfsizlik'}, {at: 40, text: 'Shaxsiy daxlsizlik'}, {at: 80, text: 'Siyosiy imij'}]} footer={{at: rel(281.2, 275.9), text: 'Aniq sabablar haqida faqat taxmin qilish mumkin'}} />
		),
	},
	/* ------------------------------ CHAPTER 4 ------------------------------ */
	{
		from: 284.2, to: 287.5, id: 'ch4', desc: 'To‘rtinchi sir: oddiy ayoldan millionergacha.',
		visual: 'Bob kartasi', media: ['spb.jpg'], sfx: 'whoosh',
		render: () => <ChapterCard n="4" title="Oddiy ayoldan millionergacha" bg={<PhotoShot src="spb.jpg" fit="cover" />} />,
	},
	{
		from: 287.5, to: 293.5, id: 'proekt', desc: '2020-yilda «Proyekt» surishtiruvi.',
		visual: 'Hujjat kartasi: «Proyekt», 25.11.2020', media: [],
		render: () => (
			<DocCard outlet="«PROYEKT» (PROEKT)" date="25-noyabr, 2020" headline="Mustaqil jurnalistik loyiha yangi surishtiruv e’lon qildi" status="investigation" />
		),
	},
	{
		from: 293.5, to: 297.9, id: 'krivonogikh', desc: 'Svetlana Krivonogix.',
		visual: 'Ism kartasi (litsenziyali fotosurat topilmadi)', media: [],
		render: () => <NameCards status="investigation" names={[{name: 'Svetlana Krivonogix', sub: 'Surishtiruv markazidagi shaxs', at: 6}]} />,
	},
	{
		from: 297.9, to: 302.1, id: 'spb', desc: 'Sankt-Peterburgda kamtarona sharoitda o‘sgan.',
		visual: 'Sankt-Peterburg, Neva va Ermitaj', media: ['spb.jpg'],
		render: () => (
			<>
				<PhotoShot src="spb.jpg" fit="cover" from={{x: 0, y: 0, s: 1.02}} to={{x: -50, y: 0, s: 1.1}} />
				<LowerThird name="Sankt-Peterburg" role="Krivonogix o‘sgan shahar" delay={6} />
				<Credit text="Foto: Ad Meskens · Wikimedia Commons · CC BY-SA 4.0" />
			</>
		),
	},
	{
		from: 302.1, to: 309.6, id: 'assets', desc: 'Ko‘chmas mulk, biznes aktivlari, yirik bank.',
		visual: 'Chips: aktivlar turlari', media: [],
		render: () => (
			<Chips status="investigation" title="«Proyekt» hujjatlarida tilga olingan" items={[{at: rel(303.6, 302.1), text: 'Qimmatbaho ko‘chmas mulk'}, {at: rel(305.5, 302.1), text: 'Biznes aktivlari'}, {at: rel(306.9, 302.1), text: 'Yirik bank ulushi'}]} />
		),
	},
	{
		from: 309.6, to: 316.8, id: 'money', desc: 'Taxminan 100 million dollar.',
		visual: 'Hisoblagich $100 000 000', media: [],
		render: () => <Counter to={100000000} prefix="≈ $" label="«PROYEKT» BAHOSI" note="O‘sha paytdagi hisob-kitoblar bo‘yicha" status="investigation" />,
	},
	{
		from: 316.8, to: 332.0, id: 'elizaveta', desc: '2003-yilda tug‘ilgan qizi Yelizaveta; otalik isbotlanmagan.',
		visual: 'Ism kartasi (surat ishlatilmaydi) + TASDIQLANMAGAN', media: [],
		render: () => (
			<NameCards status="unconfirmed" caption="Otalik haqidagi taxmin mustaqil ravishda isbotlanmagan" names={[{name: 'Yelizaveta', sub: '2003-yilda tug‘ilgan · «Proyekt» surishtiruvi', at: rel(322.4, 316.8)}]} />
		),
	},
	{
		from: 332.0, to: 337.7, id: 'peskov', desc: 'Peskov da’volarni asossiz deb rad etgan.',
		visual: 'Dmitriy Peskov, Kreml, 21.03.2023 (Kremlin.ru)', media: ['peskov_2023.jpg'],
		render: () => (
			<>
				<PhotoShot src="peskov_2023.jpg" frame from={{x: 0, y: 30, s: 1.0}} to={{x: 0, y: 0, s: 1.08}} />
				<LowerThird name="Dmitriy Peskov" role="Kreml matbuot kotibi: «da’volar asossiz»" delay={6} />
				<Credit text={KREMLIN + ' · 21.03.2023'} />
			</>
		),
	},
	{
		from: 337.7, to: 347.8, id: 'wealth-q', desc: 'Qanday qilib yaqin insonlar ulkan boyliklarga ega bo‘ldi?',
		visual: 'Savol, Sankt-Peterburg fonida', media: ['spb.jpg'],
		render: () => (
			<>
				<PhotoShot src="spb.jpg" fit="cover" from={{x: 0, y: 0, s: 1.15}} to={{x: 60, y: 0, s: 1.2}} dim={0.7} />
				<BigText title="Prezidentga yaqin insonlar qanday qilib ulkan boylikka ega bo‘ldi?" size={78} />
			</>
		),
	},
	{
		from: 347.8, to: 356.2, id: 'power', desc: 'Hokimiyat, moliyaviy aloqalar, manfaatlar to‘qnashuvi.',
		visual: 'Chips', media: [],
		render: () => (
			<Chips items={[{at: rel(350.9, 347.8), text: 'Hokimiyat'}, {at: rel(352.5, 347.8), text: 'Moliyaviy aloqalar'}, {at: rel(354.0, 347.8), text: 'Manfaatlar to‘qnashuvi'}]} title="Bu faqat shaxsiy munosabatlar haqida emas" />
		),
	},
	/* ------------------------------ CHAPTER 5 ------------------------------ */
	{
		from: 356.2, to: 359.4, id: 'ch5', desc: 'Beshinchi sir: Putinning qizlari kim?',
		visual: 'Bob kartasi', media: ['family2002_1.jpg'], sfx: 'whoosh',
		render: () => <ChapterCard n="5" title="Putinning qizlari kim?" bg={<PhotoShot src="family2002_1.jpg" fit="cover" />} />,
	},
	{
		from: 359.4, to: 364.7, id: 'daughters', desc: 'Ikki qizi haqida juda kam ma’lumot berilgan.',
		visual: 'Kreml tarqatgan 2002-yilgi oilaviy surat (yuzlar ko‘rsatilmagan)', media: ['family2002_1.jpg'],
		render: () => (
			<>
				<PhotoShot src="family2002_1.jpg" from={{x: 0, y: 0, s: 1.1}} to={{x: 30, y: 0, s: 1.2}} />
				<Credit text={KREMLIN + ' · 2002'} />
			</>
		),
	},
	{
		from: 364.7, to: 373.8, id: 'names', desc: 'Mariya Vorontsova va Katerina Tixonova.',
		visual: 'Ism kartalari', media: [],
		render: () => (
			<NameCards status="fact" names={[{name: 'Mariya Vorontsova', sub: 'Tibbiyot va ilmiy loyihalar (genetika)', at: rel(366.0, 364.7)}, {name: 'Katerina Tixonova', sub: 'Ilmiy va texnologik loyihalar', at: rel(368.0, 364.7)}]} caption="Xalqaro matbuot va AQSH hukumati hujjatlaridagi ismlar" />
		),
	},
	{
		from: 373.8, to: 378.0, id: 'tikhonova', desc: 'Katerina — ilmiy va texnologik loyihalar.',
		visual: 'Katerina Tixonova videoaloqa orqali, Rossiya–Afrika forumi vazirlar konferensiyasi, 09.11.2024', media: ['tikhonova_2024.jpg'],
		render: () => (
			<>
				<PhotoShot src="tikhonova_2024.jpg" frame from={{x: 0, y: 0, s: 1.0}} to={{x: 0, y: -10, s: 1.08}} />
				<LowerThird name="Katerina Tixonova" role="09.11.2024 · forumda videoaloqa orqali" delay={4} />
				<Credit text="Foto: Ye. Lyzlova / Roscongress · edu.gov.ru (CC BY 4.0)" />
			</>
		),
	},
	{
		from: 378.0, to: 387.6, id: 'sanctions', desc: '2022-yilda AQSH ikkalasiga sanksiya joriy qildi.',
		visual: 'AQSH Moliya vazirligi press-relizi, 06.04.2022 (asl hujjat)', media: ['treasury_para.png'], sfx: 'impact',
		render: () => (
			<DocImage src="treasury_para.png" header="AQSH MOLIYA VAZIRLIGI · OFAC" date="6-aprel, 2022" status="fact" caption="Press-reliz JY0705 · home.treasury.gov · AQSH hukumati hujjati (public domain)" />
		),
	},
	{
		from: 387.6, to: 398.6, id: 'careful', desc: 'Putin farzandlari haqida doimo ehtiyotkor.',
		visual: 'Putin minbarda (Kremlin.ru video)', media: ['v_may9_podium.mp4', 'v_may9_podium3.mp4'],
		render: () => (
			<>
				<Sequence durationInFrames={s(6)}><VideoShot src="v_may9_podium.mp4" startFrom={2} zoom={[1.1, 1.2]} origin="50% 40%" /></Sequence>
				<Sequence from={s(6)}><VideoShot src="v_may9_podium3.mp4" startFrom={3} zoom={[1.15, 1.25]} origin="50% 30%" /></Sequence>
				<Credit text={KREMLIN_V} />
			</>
		),
	},
	{
		from: 398.6, to: 403.3, id: 'big-q', desc: 'Eng katta savol: nega bunchalik maxfiylik?',
		visual: 'Sarlavha', media: [], sfx: 'impact',
		render: () => (<><QuestionMarks /><BigText kicker="ENG KATTA SAVOL" title="Nega bunchalik maxfiylik?" size={110} /></>),
	},
	{
		from: 403.3, to: 428.2, id: 'two-worlds', desc: 'Bir tomonda siyosiy hayot, ikkinchi tomonda yopiq shaxsiy hayot.',
		visual: 'Split: siyosiy hayot (Kremlin.ru videolari) | shaxsiy hayot (yuzlar yashirilgan oilaviy surat)', media: ['v_awards_putin2.mp4', 'v_presser_close.mp4', 'family2002_1.jpg'],
		render: () => (
			<SplitScreen
				left={
					<>
						<Sequence durationInFrames={s(8.8)}><VideoShot src="v_awards_putin2.mp4" startFrom={7.5} zoom={[1.1, 1.15]} origin="50% 35%" /></Sequence>
						<Sequence from={s(8.8)}><VideoShot src="v_presser_close.mp4" startFrom={0} zoom={[1.2, 1.3]} origin="50% 35%" /></Sequence>
					</>
				}
				right={<PhotoShot src="family2002_1.jpg" fit="cover" from={{x: 0, y: 0, s: 1.3}} to={{x: 0, y: 0, s: 1.4}} dim={0.35} />}
				leftLabel="SIYOSIY HAYOT"
				rightLabel="SHAXSIY HAYOT"
				rightAt={rel(412.2, 403.3)}
			/>
		),
	},
	{
		from: 428.2, to: 445.8, id: 'privacy', desc: 'Daxlsizlik huquqi va jamoatchilik manfaati.',
		visual: 'Ikki tamoyil kartasi', media: [],
		render: () => (
			<Chips title="Ikki tamoyil" items={[{at: 30, text: 'Shaxsiy hayot daxlsizligi'}, {at: rel(440, 428.2), text: 'Jamoatchilik manfaati'}]} footer={{at: rel(434, 428.2), text: 'Yaqinlari katta aktivlar va davlat loyihalari bilan bog‘liq bo‘lsa-chi?'}} />
		),
	},
	{
		from: 445.8, to: 451.7, id: 'journalists', desc: 'Mustaqil jurnalistlar aloqalarni tekshiradi.',
		visual: 'Matbuot zali (Kremlin.ru video)', media: ['v_presser_hall.mp4'],
		render: () => (<><VideoShot src="v_presser_hall.mp4" startFrom={3} zoom={[1.1, 1.2]} /><Credit text={KREMLIN_V} /></>),
	},
	{
		from: 451.7, to: 468.7, id: 'evidence', desc: 'Surishtiruv ≠ isbotlangan fakt; dalillar; taxmin ≠ haqiqat.',
		visual: 'Chips', media: [],
		render: () => (
			<Chips
				title="Surishtiruv ≠ isbotlangan fakt"
				status="investigation"
				items={[{at: rel(456.2, 451.7), text: 'Hujjatlar'}, {at: rel(457.2, 451.7), text: 'Guvohliklar'}, {at: rel(458.2, 451.7), text: 'Moliyaviy ma’lumotlar'}]}
				footer={{at: rel(461.5, 451.7), text: 'Har bir taxminni haqiqat sifatida taqdim etib bo‘lmaydi'}}
			/>
		),
	},
	{
		from: 468.7, to: 479.4, id: 'problem', desc: 'Eng katta muammolardan biri; javobsiz savollar.',
		visual: 'Putin yaqin plan (Kremlin.ru video)', media: ['v_presser_close2.mp4', 'v_presser_close.mp4'],
		render: () => (
			<>
				<Sequence durationInFrames={s(3.3)}><VideoShot src="v_presser_close2.mp4" startFrom={7.6} zoom={[1.05, 1.1]} /></Sequence>
				<Sequence from={s(3.3)}><VideoShot src="v_presser_close.mp4" startFrom={6} zoom={[1.1, 1.25]} origin="50% 35%" /></Sequence>
				<Credit text={KREMLIN_V} />
			</>
		),
	},
	/* ------------------------------ RECAP ------------------------------ */
	{
		from: 479.4, to: 494.5, id: 'recap', desc: 'Bugun ko‘rib chiqdik…',
		visual: 'Vaqt chizig‘i', media: [],
		render: () => (
			<Timeline
				events={[
					{year: '1983', text: 'Nikoh', status: 'fact', at: rel(481.5, 479.4)},
					{year: '2008', text: 'Gazeta xabari', status: 'unconfirmed', at: rel(485.3, 479.4)},
					{year: '2013', text: 'Ajrashuv e’loni', status: 'fact', at: rel(483.5, 479.4)},
					{year: '2020', text: '«Proyekt»', status: 'investigation', at: rel(490.5, 479.4)},
					{year: '2022', text: 'AQSH sanksiyalari', status: 'fact', at: rel(491.5, 479.4)},
					{year: '2024', text: 'Dossier Center', status: 'investigation', at: rel(488.0, 479.4)},
					{year: '2026', text: '«Sistema»', status: 'investigation', at: rel(489.0, 479.4)},
				]}
			/>
		),
	},
	{
		from: 494.5, to: 505.7, id: 'recap-legend', desc: 'Ayrimlari tasdiqlangan, ayrimlari surishtiruv, boshqalari tasdiqlanmagan.',
		visual: 'Legenda (qayta)', media: [],
		render: () => <Legend times={[2, rel(498.3, 494.5), rel(501.8, 494.5)]} />,
	},
	{
		from: 505.7, to: 518.2, id: 'conclusion', desc: 'Shaxsiy hayot kam yoritilgan; e’tiborni tortishi mumkin.',
		visual: 'Putin (Kremlin.ru video)', media: ['v_awards_putin2.mp4', 'v_may9_podium2.mp4'],
		render: () => (
			<>
				<Sequence durationInFrames={s(4.4)}><VideoShot src="v_awards_putin2.mp4" startFrom={7.5} zoom={[1.0, 1.08]} /></Sequence>
				<Sequence from={s(4.4)}><VideoShot src="v_may9_podium2.mp4" startFrom={2} zoom={[1.0, 1.15]} origin="50% 35%" /></Sequence>
				<Credit text={KREMLIN_V} />
			</>
		),
	},
	{
		from: 518.2, to: 530.0, id: 'cta-q', desc: 'Sizningcha… qanchalik oshkora bo‘lishi kerak?',
		visual: 'Savol kartasi', media: [],
		render: () => (<><QuestionMarks /><BigText kicker="SIZNINGCHA" title="Davlat rahbarining shaxsiy hayoti qanchalik oshkora bo‘lishi kerak?" size={80} /></>),
	},
	{
		from: 530.0, to: 545.0, id: 'end', desc: 'Fikringizni izohlarda yozib qoldiring…',
		visual: 'Yakuniy karta + manbalar', media: ['v_awards_hall.mp4'],
		render: () => (
			<>
				<VideoShot src="v_awards_hall.mp4" startFrom={2} blur={10} dim={0.72} />
				<BigText title="Fikringizni izohlarda yozib qoldiring" sub="Manbalar: Kremlin.ru · AQSH Moliya vazirligi · Dossier Center · RFE/RL «Sistema» · «Proyekt»" size={84} />
			</>
		),
	},
];

export const TOTAL_SECONDS = 545;

export const SceneTrack: React.FC = () => (
	<>
		{SCENES.map((sc) => (
			<Sequence key={sc.id} from={s(sc.from)} durationInFrames={s(sc.to) - s(sc.from)} name={sc.id}>
				<AbsoluteFill>{sc.render()}</AbsoluteFill>
			</Sequence>
		))}
	</>
);
