# Puheentunnistusohjelma

Paikallisesti suoritettava, GPU-kiihdytetty puheentunnistuksen työpöytäsovellus Windowsille. Muuntaa puhutun äänen tekstiksi, tunnistaa yksittäiset puhujat, kääntää tuloksen tarvittaessa ja toimittaa tulosteen useissa määritettävissä olevissa muodoissa.

**Versio 1.0** — julkaistu 21.5.2026

[English](README.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Русский](README.ru.md) | [简体中文](README.zh_CN.md) | [繁體中文](README.zh_TW.md)

---

## Ominaisuudet

- Puheesta tekstiksi faster-whisper-kirjaston avulla (CUDA-kiihdytys; CPU-varatoiminto tuettu)
- Puhujaeriyttäminen pyannote.audio-kirjaston avulla — jopa 10 samanaikaista puhujaa
- Paikallinen käännös (Helsinki-NLP OPUS-MT, offline) tai verkossa (Google Translate)
- Tulostusmuodot: pelkkä teksti, DOCX, SRT-tekstitykset, JSON, leikepöytä
- Eräkäsittely tiedostoille FIFO-jonolla
- Ääniprofiilikirjasto: tallenna ja tunnista nimetyt puhujat istuntojen välillä
- Puhujaryhmien hallinta kontekstikohtaista tunnistamista varten
- Määritettävät globaalit pikanäppäimet (koko järjestelmässä, myös pienennettynä)
- Tavallinen ja Lyhytistunto-tallennustilat
- GUI (CustomTkinter) ja täysi CLI-tila
- Järjestelmäpalkki-integraatio ilmoitusten kanssa
- Istuntohistoria takautuvalla tulosteen uudelleenluonnilla
- Kaikkien käyttäjätietojen varmuuskopiointi ja palauttaminen

---

## Järjestelmävaatimukset

| Vaatimus | Tiedot |
|----------|--------|
| Käyttöjärjestelmä | Windows 10 tai 11, 64-bittinen |
| GPU | NVIDIA-näytönohjain CUDA-tuella suositellaan (RTX 3060 Ti tai parempi); CPU-varatoiminto tuettu |
| RAM | Vähintään 4 Gt; 8 Gt suositellaan yli 30 minuutin tiedostoille |
| Levytila | 10 Gt vapaata (sisältää kaikki Whisper-mallien koot ja OPUS-MT-kieliparit) |
| VLC | Vaaditaan äänentoistoon — asennusohjelma lataa VLC:n automaattisesti, jos se puuttuu |
| FFmpeg | Vaaditaan MP4/AVI-purkamiseen — oltava PATH-muuttujassa, kun käytetään lähdekoodia |

---

## Pika-aloitus — Asennusohjelma

1. Lataa `wsp_setup.exe` [uusimmasta GitHub-julkaisusta](../../releases/latest).
2. Suorita asennusohjelma ja seuraa ohjattua toimintoa:
   - Valitse Whisper-malli (Medium suositellaan).
   - Hyväksy HuggingFace pyannote -lisenssi, jos haluat puhujantunnistuksen.
3. Käynnistä **Puheentunnistusohjelma** työpöydän pikakuvakkeesta tai Käynnistä-valikosta.
4. Valitse syöttölaite tai vedä äänitiedosto eräjonoon ja paina **Aloita**.

---

## Pika-aloitus — Lähdekoodista

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **Huomio:** PyAudio vaatii Microsoft C++ Build Tools -työkalut ja PortAudion vcpkg:n kautta ennen `pip install` -komentoa.
> Katso `requirements.txt`-tiedoston alun kommentit vaiheittaisista ohjeista.
> FFmpeg täytyy olla asennettuna järjestelmään ja PATH-muuttujassa.

---

## Komentorivin käyttö

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

Täydellinen parametriviite ja poistumiskoodit, katso [docs/CLI.md](docs/CLI.md).

---

## Käyttöliittymäkielet

Englanti, saksa, espanja, suomi, venäjä, yksinkertaistettu kiina, perinteinen kiina.

> Venäjän- ja kiinankieliset käännökset ovat automatisoituja. Äidinkielisten puhujien tarkistus on kesken.

---

## Dokumentaatio

| Asiakirja | Kuvaus |
|-----------|--------|
| [docs/Specification.md](docs/Specification.md) | Täydellinen tekninen määrittely (v1.0) |
| [docs/WorkPlan.md](docs/WorkPlan.md) | Vaiheittainen työsuunnitelma (vaiheet 0–9) |
| [docs/CLI.md](docs/CLI.md) | Komentorivin parametriviite |
| [docs/BUILD.md](docs/BUILD.md) | Asennusohjelman koostamisohjeet (lähdekoodista) |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | Ääniprofiilin `speaker.json`-muoto |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | Istuntohistorian JSON-muoto |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | V1.0:n julkaisutiedot |

---

## Kirjastot

Kaikki kirjastot ovat ilmaisia ja avoimen lähdekoodin. Kiinnitetyt versiot, katso `requirements.txt`.

| Kirjasto | Rooli | Lisenssi |
|----------|-------|---------|
| faster-whisper | Puheesta tekstiksi ja kielen tunnistus | MIT |
| pyannote.audio | Puhujaeriyttäminen (HuggingFace-lisenssi vaaditaan) | MIT |
| CustomTkinter | Graafinen käyttöliittymä | MIT |
| pyaudio | Mikrofoni- ja web-kamera-äänen tallennus | MIT |
| OpenCV | Web-kameran videovirran käyttö | Apache 2.0 |
| keyboard | Globaalit pikanäppäimet | MIT |
| transformers + sentencepiece | Helsinki-NLP OPUS-MT paikallinen käännös | Apache 2.0 |
| python-vlc | Äänen/videon toisto | LGPL 2.1 |
| python-docx | DOCX-tulostus | MIT |
| PyInstaller | Sovelluksen paketointi | GPL + käynnistyslataurin poikkeus |
| Inno Setup | Windows-asennusohjelma (erillinen työkalu) | Inno Setup -lisenssi |
| PyTorch | Syväoppimisen suoritusympäristö | BSD 3-Clause |

> **HuggingFace-lisenssi:** pyannote.audio vaatii HuggingFace-mallilisenssin hyväksymistä.
> Jos ei hyväksytä, puhujantunnistus on poistettu käytöstä ja kaikki puhujat merkitään Tuntematon.

---

## Osallistuminen / Ongelmat

Tämä on yksityinen tietovarasto. Ilmoita virheestä tai pyydä ominaisuutta avaamalla issue GitHubissa.
