# AppArmor-voorstel voor bwrap — 2026-10-21 UTC

## Revisie R2 — runtimeanalyse 06:35:02
De eerste tijdelijke proef is door de gebruiker uitgevoerd en mislukt; exacte exitcode ontbreekt. Beide profielen zijn volgens de gebruiker daarna verwijderd. Kandidaat hieronder is herzien, NIET opnieuw geladen. Zie docs/apparmor-bwrap-runtime-review.md voor analyse per denial, exacte diff, security-review en de leidende beperkte R2-testprocedure. De nieuwe procedure gaat vóór de oudere algemene proefbeschrijving hieronder; gebruik een nieuwe root-owned R2-kopie en bewaar de vorige kopie. Geen sys_ptrace- of SELinux-proberechten toegevoegd.

## Besluit en bewijsgrens
Voorstel: een klein, AFGEBAKEND ENFORCE-TESTPROFIEL voor /usr/bin/bwrap met een gestapeld beperkt kindprofiel. Nog NIET laden of naar /etc installeren. Geen productieklaar Codex-profiel: alleen de hieronder beschreven /usr-only tests met true/cat/sleep zijn beoogd. De oude test met --ro-bind / / en willekeurige Codex/bash/node-programma's is bewust niet vrijgegeven. Statische syntaxcontrole slaagt; werking en security-negativetests na kernelattachment zijn nog NIET bewezen. Geen globaal permissieve/unconfined- of complain-oplossing gebruiken.

Het definitieve minimale rechtenset kan zonder runtime-auditproef niet betrouwbaar worden vastgesteld. Dit voorstel minimaliseert de eerste test, niet alle toekomstige Codex-mogelijkheden. Een werkende productiesandbox vergt later een apart workloadprofiel en een nieuwe review; verbreed deze kandidaat niet automatisch als een test faalt.

## Lokaal vastgestelde toestand
- bubblewrap 0.9.0-1ubuntu0.3 geïnstalleerd op /usr/bin/bwrap; root:root 0755, geen setuidbit en getcap gaf geen filecapabilities. AppArmor 4.0.1really4.0.1-0ubuntu0.24.04.9 en parser 4.0.1 aanwezig. apparmor-profiles niet geïnstalleerd, apparmor-utils status un.
- kernel.apparmor_restrict_unprivileged_userns=1 en kernel.unprivileged_userns_clone=1. Niets gewijzigd.
- journalctl -k bevestigt om 06:18:07 UTC: userns_create van unconfined naar unprivileged_userns; daarna DENIED setpcap en DENIED open proc/25226/uid_map met 'Failed name lookup - disconnected path'. Eerdere vergelijkbare melding om 05:12:31. Geen nieuwe sandboxtest gestart tijdens dit onderzoek.
- /etc/apparmor.d/unprivileged_userns bevat audit deny capability en audit deny change_profile. Een allow toevoegen aan een gestapeld profiel heft een bestaande expliciete deny niet op: de juiste executable-attachment/labelroute moet dus later aantoonbaar worden gecontroleerd.
- Kernel features domain/stack=yes, domain/post_nnp_subset=yes en domain/disconnected.path=yes; namespaces/mask bevat userns_create. Dat is interfaceondersteuning, geen bewijs dat de kandidaat al geladen is.

## Officiële distributieprofielen eerst onderzocht
Via apt-get download is alleen apparmor-profiles 4.0.1really4.0.1-0ubuntu0.24.04.9 opgehaald uit de bestaande Ubuntu noble-updates-bron. dpkg-deb -x heeft het pakket uitsluitend onder inventory/apparmor-review/extracted uitgepakt. Geen package-installatie, maintainer-script, profielreload of sudo uitgevoerd.

Daarin staat /usr/share/apparmor/extra-profiles/bwrap-userns-restrict. De distributieversie verklaart expliciet dat zij vrijwel alles toestaat. Zij gebruikt een parent met alle capabilities en brede file/network/mount-rechten, en een gestapeld kind dat capabilities weigert. Het kindstack-principe is nuttig vanwege no_new_privs; de brede allow-regels voldoen niet aan deze opdracht. Daarom niet blind kopiëren, ook niet alleen omdat het een officieel profiel is. Ubuntu-release notes beschrijven daarnaast unconfined+userns als compatibiliteitsoptie: die optie is hier expliciet uitgesloten.

SHA256 gedownload pakket: 90b02aa006eea7702cd4e851343e469e41365dda42145a3cb035de1d6c773b8c.
SHA256 distributie-extra-profiel: 11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9.
De exacte bronkopieën blijven lokaal in genegeerde inventory/; geen brede upstream-profielen in de actieve policyboom geplaatst.

## Regelkeuzes en verwacht beveiligingseffect
- Exact executable-attachment /usr/bin/bwrap, twee unieke profielnamen server5-bwrap en server5-bwrap-child. Dit geldt bij latere attachment voor ALLE bwrap-aanroepen op deze host, niet alleen Codex of mau. Confined callers met eigen ix/px-policy kunnen anders uitkomen; controleer labels en conflicten. Niets aan gebundelde bwrap-paden toevoegen.
- userns in parent voorkomt beoogd de generieke unprivileged_userns-route voor deze executable. setpcap correspondeert met de aangetroffen capability-denial en bwrap PR_CAPBSET_DROP; sys_admin is nodig voor de namespace-mount/pivotopbouw. Deze regels staan gebruik toe wanneer de kernel die capability werkelijk bezit, ze verlenen op zichzelf geen host-rootcapabilities. Test bwrap uitsluitend als niet-root mau. net_admin, sys_ptrace, sys_chroot, setuid/setgid, dac_override en alle andere capabilities krijgen in deze eerste kandidaat geen allow. Extra use-cases zoals loopbackconfiguratie/netwerknamespace of uidwissels vallen erbuiten.
- owner-procregels beperken schrijfaccess tot uid_map, gid_map en setgroups voor numerieke PID/self-paden. Kernel/DAC/usernamespace-IDmapvoorwaarden blijven gelden. owner betekent dezelfde bestandseigenaar, NIET 'alleen mijn kindproces'; @{pid} is op deze host een numeriek patroon, geen runtime-PID-identiteit. Statische policy kan daarmee geen procesafstamming garanderen. Geen /proc/** rw, geen sysctl-schrijfregels.
- De kernelmelding is een disconnected-path-fout: een gewone /proc-regel alleen lost dat niet noodzakelijk op. Ongekwalificeerd attach_disconnected kan objecten onder / laten aliassen; de AppArmor-manpage waarschuwt dat dit een onveilige ontwikkeloptie is. Daarom uitsluitend attach_disconnected.path=/att/server5-bwrap/ met beperkte expliciete regels voor de detached procobjecten. De parser en kernelfeature ondersteunen dit. Dat beperkt naamaliasing, bewijst geen afwezigheid van aliasing; de prefix moet afwezig/reserved blijven en is geen echte directory om aan te maken. Andere disconnected objecten blijven standaard geweigerd. Geen terugval naar algemeen attach_disconnected bij fouten.
- mediate_deleted laat ook verwijderde objecten bemiddelen. Mountregels benoemen de root-propagatie, tijdelijke tmpfs op /tmp, stagingroot, /usr-bindbron, read-only remount, proc en pivots/unmounts. De remount eist ro en specifieke flags, passend bij de huidige rw,relatime-rootmount. Geen algemene mount/umount/pivot_root-allow. Relatieve/gedetacheerde padnamen kunnen in runtime anders blijken; dan afbreken en audit beoordelen, niet blind /** toestaan.
- Geen abstractions/base: die is lokaal onderzocht en bevat onder meer brede library-/private-home-/IPC-regels. Alleen loader/librarytoegang, vaste stagingpaden en noodzakelijke proc-readregels toegevoegd. Geen home-, SSH-, Codex-auth-, algemene /etc- of hostdata-toegang.
- Parent kan alleen true/cat/sleep exec'en en alleen met de verplichte NNP-stack server5-bwrap//&server5-bwrap-child. Geen ix- of unconfined-fallback. Het kind heeft expliciete capability/userns/mount/network/ptrace-denies en geen verdere exec-rule. Een AppArmor-capability-deny blokkeert gebruik; hij wist niet zelf de Linux capability-bitsets. Nulbitsets in de standaardproef moeten uit bwrap zelf voortkomen en worden afzonderlijk gemeten. NNP en stacking zijn gebaseerd op het distributiepatroon; de compiler herkent de targetnaam. Runtime moet bewijzen dat de bedoelde stack werkelijk ontstaat en geen capabilities behoudt.
- File-/mountrechten zijn pathname- en namespacegevoelig, geen cryptografische binaire allowlist. Een privileged actor die namespace-inhoud wijzigt blijft een risico; dit profiel is geen grens tegen host-root. Standaard deny voor overige handelingen kan bestaande bwrap-workloads breken. Daarom alleen een gecontroleerde tijdelijke proef, geen persistente uitrol.

## Exact kandidaatbestand
Bron: /home/mau/server5-commandcenter/config/apparmor/server5-bwrap
Beoogde testkopie na aparte toestemming: /root/server5-apparmor-review/server5-bwrap
Eventuele latere persistente bestemming, nu NIET gebruiken: /etc/apparmor.d/server5-bwrap
SHA256 bron: 9e84a1ab68b27c9ab0caefcccb03122819fc05e0edcd3c5f53a22cfb3e9978c2.

```apparmor
# Draft: bounded /usr-only smoke tests, NOT a production Codex profile.
# Load only after review and explicit approval. No kernel load during compilation.
abi <abi/4.0>,
include <tunables/global>

profile server5-bwrap /usr/bin/bwrap flags=(attach_disconnected.path=/att/server5-bwrap/,mediate_deleted) {
  userns,
  capability setpcap,
  capability sys_admin,

  /usr/bin/bwrap mr,
  /usr/bin/{true,cat,sleep} mr,
  /etc/ld.so.cache r,
  /{,usr/}lib{,64}/**.so* mr,
  /usr/lib/locale/** r,

  / r,
  /usr/ r,
  /proc/ r,
  /tmp/ r,
  /proc/sys/kernel/{overflowuid,overflowgid,cap_last_cap} r,
  /proc/sys/user/max_user_namespaces r,
  owner /proc/{self,@{pid}}/ r,
  # Directory enumeration only, for fdwalk/close_extra_fds; no fd/* access.
  owner /proc/{self,@{pid}}/fd/ r,
  owner /proc/{self,@{pid}}/{mountinfo,status,stat} r,
  owner /proc/{self,@{pid}}/attr/current r,
  owner /proc/{self,@{pid}}/ns/{user,mnt,pid,cgroup} r,
  owner /proc/{self,@{pid}}/{uid_map,gid_map,setgroups} rw,
  # Explicit isolated prefix for disconnected proc objects; never attach at /.
  owner /att/server5-bwrap/proc/{self,@{pid}}/ r,
  owner /att/server5-bwrap/proc/{self,@{pid}}/{uid_map,gid_map,setgroups} rw,
  owner /att/server5-bwrap/proc/{self,@{pid}}/{mountinfo,status,stat} r,
  owner /att/server5-bwrap/proc/{self,@{pid}}/attr/current r,
  owner /att/server5-bwrap/proc/{self,@{pid}}/ns/{user,mnt,pid,cgroup} r,

  # Only fixed root-staging entries; no arbitrary /tmp/** write rule.
  /tmp/{newroot,oldroot}/ rw,
  /tmp/newroot/{usr,proc,tmp}/ rw,
  /tmp/newroot/{bin,lib,lib64} w,
  /{newroot,oldroot}/ rw,
  /newroot/{usr,proc,tmp}/ rw,
  /newroot/{bin,lib,lib64} w,
  /oldroot/usr/ r,

  # bwrap 0.9.0 setup sequence, restricted by operation/source/destination.
  mount options=(rw,silent,rslave) -> /,
  mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /tmp/,
  mount options=(rw,silent,rbind) /tmp/newroot/ -> /tmp/newroot/,
  pivot_root oldroot=/tmp/oldroot/ /tmp/,
  mount options=(rw,silent,rbind) /oldroot/usr/ -> /newroot/usr/,
  mount options=(ro,silent,remount,bind,nosuid,nodev,relatime) -> /newroot/usr/,
  mount fstype=proc options=(rw,nosuid,nodev,noexec) proc -> /newroot/proc/,
  mount options=(rw,silent,rprivate) -> /oldroot/,
  umount /oldroot/,
  pivot_root oldroot=/newroot/ /newroot/,
  umount /,

  # Receive termination from the invoking shell and signal own helper processes.
  signal (receive) peer=unconfined,
  signal (send,receive) peer=server5-bwrap,
  signal (send,receive) peer=server5-bwrap//&server5-bwrap-child,
  ptrace (read) peer=server5-bwrap,

  # No inherited-capability fallback and no unconfined transition.
  /usr/bin/{true,cat,sleep} px -> server5-bwrap//&server5-bwrap-child,
}

# Stacked with the parent because bwrap sets no_new_privs.
profile server5-bwrap-child flags=(attach_disconnected.path=/att/server5-bwrap/,mediate_deleted) {
  /usr/bin/{true,cat,sleep} mr,
  /etc/ld.so.cache r,
  /{,usr/}lib{,64}/**.so* mr,
  /usr/lib/locale/** r,
  owner /proc/{self,@{pid}}/{status,stat} r,
  owner /proc/{self,@{pid}}/attr/current r,
  owner /att/server5-bwrap/proc/{self,@{pid}}/{status,stat} r,
  owner /att/server5-bwrap/proc/{self,@{pid}}/attr/current r,
  signal (receive) peer=unconfined,
  signal (send,receive) peer=server5-bwrap,
  signal (send,receive) peer=server5-bwrap//&server5-bwrap-child,

  audit deny capability,
  audit deny userns,
  audit deny mount,
  audit deny umount,
  audit deny pivot_root,
  audit deny network,
  audit deny ptrace,
}
```

## Reeds uitgevoerde controles — geen policy geladen
Op server5 als mau:

```bash
apparmor_parser --skip-kernel-load --skip-cache --Werror \
  -I /etc/apparmor.d \
  /home/mau/server5-commandcenter/config/apparmor/server5-bwrap
apparmor_parser --skip-kernel-load --skip-cache --names \
  -I /etc/apparmor.d \
  /home/mau/server5-commandcenter/config/apparmor/server5-bwrap
```

Exit 0, geen waarschuwingen. Namen: server5-bwrap en server5-bwrap-child. Ook zonder kernelload naar inventory/apparmor-review/candidate.bin gecompileerd en preprocessed output opgeslagen. Binary bevat de geïsoleerde disconnected-prefix en expliciete stacktarget. --skip-kernel-load (-Q) verhindert laden; --skip-cache (-K) verhindert policycachelezen/-schrijven. Geen sudo nodig voor deze controles. Syntax/serialisatie is geen runtimeacceptatie. Een statische contractcheck controleert daarnaast dat geen globale allow/unconfined/complain/execfallback en uitsluitend twee expliciete parentcapabilities zijn opgenomen.

## Latere handmatige sudo-proef — NIET uitgevoerd, vereist nieuwe toestemming
Begin in een aparte bestaande LAN-SSH-terminal. Laat huidige Codex-sessie en netwerk ongemoeid. Controleer eerst bestaande geladen namen/attachments en actieve bwrap-processen; laad niets bij een conflict of als andere workloads afhankelijk zijn van bwrap. De nieuwe beperkte attachment kan andere bwrap-aanroepen blokkeren. Een root-readable profielinventaris ontbreekt nog.

```bash
sudo cat /sys/kernel/security/apparmor/profiles
sudo grep -R -n '/usr/bin/bwrap' /etc/apparmor.d
pgrep -a -x bwrap
```

Een lege pgrep/grep kan exit 1 geven en is op zichzelf geen installatiefout. Controleer de uitvoer met de beheerder; automatiseer de beslissing niet. Beide server5-profielnamen moeten afwezig zijn; ook een ander exact bwrap-attachmentprofiel is een stopreden. /att/server5-bwrap mag niet bestaan en mag niet tijdens de proef als hostpad worden gemaakt. Bekijk de bron en vergelijk hash. Daarna is voor de gecontroleerde, ALLEEN RUNTIME-proef deze eenmalige sudo-handeling nodig:

```bash
sudo install -d -o root -g root -m 0700 /root/server5-apparmor-review
sudo install -o root -g root -m 0600 \
  /home/mau/server5-commandcenter/config/apparmor/server5-bwrap \
  /root/server5-apparmor-review/server5-bwrap
sudo sha256sum /root/server5-apparmor-review/server5-bwrap
sudo apparmor_parser --skip-kernel-load --skip-cache --Werror \
  -I /etc/apparmor.d /root/server5-apparmor-review/server5-bwrap
```

Stop nu voor hash-/reviewcontrole; hash moet gelijk zijn aan bovenstaande bronhash. Geen bestaand /root-bestand overschrijven: als de testmap/bestandsnaam al bestaat, eerst afzonderlijk beoordelen/archiveren. De install-opdrachten hierboven zijn uitsluitend voor een tevoren vastgestelde nieuwe locatie. Pas na die controle:

```bash
sudo apparmor_parser --add --skip-cache -I /etc/apparmor.d \
  /root/server5-apparmor-review/server5-bwrap
sudo cat /sys/kernel/security/apparmor/profiles
```

--add mag niets vervangen; bij bestaande profielnaam stoppen, niet naar --replace wisselen. Dit laadt twee profielen in de kernel zonder globale reload, systeemherstart of persistent bestand in /etc. Controleer enforce-status en houd de rootkopie intact voor rollback. Alleen bestaande sudo-rechten voor install, parser en rootdiagnostiek nodig; geen NOPASSWD/sudoers-verruiming. Tijdens dit voorstel geen van deze sudo-opdrachten uitgevoerd.

## Positieve tests na een later goedgekeurde load — als mau, nooit sudo bwrap
Gebruik bewust een lege root met alleen read-only /usr; niet --ro-bind / /. Geen home/SSH/auth-mounts en geen netwerkopties. De Linux netwerknamespace wordt in deze minimale proef niet gewijzigd; parent/payload krijgen geen algemene network-allow. Dit is geen volledige netwerkkanaal-/fd-isolatietest.

```bash
/usr/bin/bwrap --unshare-user --unshare-pid --unshare-cgroup-try \
  --die-with-parent --clearenv --chdir / \
  --ro-bind /usr /usr \
  --symlink usr/bin /bin --symlink usr/lib /lib \
  --symlink usr/lib64 /lib64 --proc /proc --dir /tmp \
  /usr/bin/true
```

Verwacht: exit 0. Bekende niet-fatale SELinux-/namespaceprobedenials kunnen bewust blijven bestaan; beoordeel noodzakelijke stappen en FD-sanitatie apart volgens de R2-review, niet op auditstilte alleen. De kandidaat is niet runtimebewezen: eerste onverwachte denial betekent STOP, audit lezen en rollback; niet overschakelen naar complain/algemene allow. Exacte cgroup/mount-/disconnectedpadregels zijn te toetsen, niet verondersteld bewezen.

Herhaal dezelfde bwrap-prefix en vervang alleen het eindprogramma door elk van:

```text
/usr/bin/cat /proc/self/attr/current
/usr/bin/cat /proc/self/status
/usr/bin/sleep 20
```

Verwacht bij attr/current de stack met beide namen en enforce, nooit unconfined/unprivileged_userns als enige profiel. Bij status: uid passend gemapt, NoNewPrivs 1 en CapInh/CapPrm/CapEff/CapAmb nul; CapBnd afzonderlijk beoordelen, niet als actuele effective capabilities interpreteren. Tijdens sleep kan beheerder met /proc/<payloadpid>/attr/current dezelfde stack inspecteren. Het gegeven PID moet van de echte payload zijn, niet de bwrap-monitor. Eventuele denial bij label/statusinspectie is nog geen werkende proef; inspecteer van buiten met root en beoordeel of verdere readregels überhaupt nodig zijn.

## Negatieve tests en auditacceptatie
Met dezelfde bwrap-prefix, afzonderlijke runs:
- /usr/bin/id als eindprogramma: exec moet geweigerd worden; geen fallback naar unconfined/inherit.
- /usr/bin/cat /usr/share/dpkg/ostable: controleer eerst buiten bwrap dat het bestand voor mau bestaat/leesbaar is; binnen de sandbox hoort lezen door de filepolicy te falen. Zo wordt echte confinement getest, niet uitsluitend DAC of een ontbrekend bestand.
- --cap-add SYS_ADMIN vóór het eindprogramma mag nooit een payload met bruikbare CapEff/CapPrm opleveren; als het initpad of de capabilitycontrole faalt is dat veiliger, maar geen vervanging voor stackvalidatie. Geen willekeurige caphelper of shell vrijgeven om deze test te laten slagen.

```bash
sudo journalctl -k --since '<UTC-starttijd van proef>' --no-pager
```

Filter/beoordeel specifiek server5-bwrap, server5-bwrap-child, unprivileged_userns, bwrap en de echte payload-PID's. Positieve tests moeten slagen; negatieve tests moeten om de bedoelde policyreden falen met passende auditcontext. Geen DENIED afwezigheid als enige bewijs gebruiken. Geen netwerk-/capability-escapes of volledige Codex-sandboxwerking geclaimd op basis van true. Voor Codex blijft aparte allowlist/profile/egress/filesystem-acceptatie nodig.

## Rollback — alleen als later werkelijk geladen
1. Stop uitsluitend de eigen true/cat/sleep-testprocessen; niet alle bwrap- of Codex-processen op de host. Houd de LAN-SSH-terminal open. Geen firewall-/AppArmor-global reload of reboot.
2. Verwijder uitsluitend de twee nieuwe profieldefinities uit de kernel met het onveranderde root-owned testbestand:

```bash
sudo apparmor_parser --remove --skip-cache -I /etc/apparmor.d \
  /root/server5-apparmor-review/server5-bwrap
sudo cat /sys/kernel/security/apparmor/profiles
```

3. Controleer dat beide namen weg zijn en dat reeds lopende testtaken geëindigd zijn. AppArmor-unload kan nog levende taken anders labelen; daarom eerst stoppen en daarna vanuit een verse normale shell controleren.
4. Root-testkopie, audit en hashes behouden voor diagnose; geen data verwijderen. Omdat er geen profiel in /etc wordt geplaatst, is geen autoloadbestand terug te draaien. Een latere persistente installatie is een afzonderlijke wijziging met eigen backup/rollback.
5. Sysctls en generiek unprivileged_userns-profiel blijven exact zoals vóór de proef. Een verse normale bwrap-aanroep kan dan weer de oorspronkelijke denial krijgen: rollback herstelt de vorige toestand, het lost de fout niet op.
6. Bij onverwachte gedeeltelijke load: loaded-namen inventariseren en alleen aanwezige nieuwe namen gericht door beheerder verwijderen; geen oude profielen vervangen. --remove-fout niet maskeren met globale unload/reload.

## Wijzigingen, risico en vervolgstap
2026-10-21: config/apparmor/server5-bwrap en deze review toegevoegd, implementatieplan/status gecorrigeerd naar bubblewrap geïnstalleerd maar runtime geblokkeerd. Reden: de audit bevestigt een specifiek AppArmor/userns-probleem. Validatie: distro-extra-profiel/broncode/manpage onderzocht; parser -Q -K --Werror exit 0; geen kernel-load, package-installatie, sysctl, SSH/netwerk- of globale AppArmor-wijzigingen. Alleen lokale onderzoeksbestanden en Git/Notion/MindMap-documentatie gewijzigd.

Risico nu: alleen conceptbestanden. Risico bij latere proef: beperkte nieuwe permissions voor bwrap, padaliasing, onvoldoende regels en compatibiliteitsbreuk voor andere callers. Daarom geen productieclaim of automatische installatie; eerst gecontroleerde runtimeproef na nieuwe toestemming. Documentatierollback: gerichte Git-revert/corrigerende publicatie; historische snapshots behouden.

## Primaire bronnen
- Ubuntu 24.04 release notes, userns restrictions: https://documentation.ubuntu.com/release-notes/24.04/
- Exacte lokale distrobron: apparmor-profiles 4.0.1really4.0.1-0ubuntu0.24.04.9, extra-profiel hierboven met SHA256; alleen opgehaald/uitgepakt.
- Upstream referentie (niet blind overgenomen): https://gitlab.com/apparmor/apparmor/-/raw/v4.0.1/profiles/apparmor/profiles/extras/bwrap-userns-restrict
- Ubuntu-manpage overeenkomstige AppArmor-versie: https://manpages.ubuntu.com/manpages/noble/man5/apparmor.d.5.html ; lokaal /usr/share/man/man5/apparmor.d.5.gz, inclusief waarschuwing attach_disconnected.
- Bubblewrap v0.9.0: https://raw.githubusercontent.com/containers/bubblewrap/v0.9.0/bubblewrap.c en bind-mount.c op dezelfde tag. Dit is upstream-brononderzoek, geen bewijs dat alle Ubuntu-patches afzonderlijk gereviewd zijn.
