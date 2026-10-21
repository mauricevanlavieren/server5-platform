# Runtime-review bwrap/AppArmor — revisie R2

Datum: 2026-10-21 UTC. Status: alleen lokale kandidaat/review gewijzigd; NIET geladen. STOP na documentatie voor ChatGPT-review en nieuwe toestemming.

## Feiten en bewijsgrens
De gebruiker meldt dat server5-bwrap en server5-bwrap-child succesvol uit de kernel verwijderd zijn. Deze sessie kan /sys/kernel/security/apparmor/profiles niet zonder root lezen en heeft geen sudo gebruikt: verwijdering wordt als gebruikersbevestiging genoteerd, niet als onafhankelijk gemeten resultaat. Geen runtimeproef gestart.

Lokale journalctl-audit bevestigt op 06:35:02 de vijf genoemde denials: filesystems en mounts read, sys_ptrace, fd-directory read (pid 25687) en mount / rw,silent,rslave (pid 25688). De oorspronkelijke commandoregel, stderr en exitcode zijn niet beschikbaar. Die exitcode is onbekend en mag niet uit auditvolgorde worden verzonnen. Wel toont de broncode welke mislukte syscall fataal is; de mountfout is een concrete noodzakelijke blokkade, ook al kunnen later nog andere blockers bestaan.

AppArmor 4.0.1really4.0.1-0ubuntu0.24.04.9, bubblewrap 0.9.0-1ubuntu0.3, libselinux1 3.5-2ubuntu2.1. ldd bevestigt de libselinux/libcap-afhankelijkheden. De bronanalyse gebruikt upstream v0.9.0 en libselinux 3.5; dit vervangt geen afzonderlijke review van alle Ubuntu-patches. Geen tracing of processtart gebruikt om extra rechten uit te lokken.

## Analyse per denial
### /proc/filesystems — niet-fatale SELinux-detectieprobe
libselinux/src/init.c: constructor init_lib roept init_selinuxmnt aan. selinuxfs_exists opent /proc/filesystems; bij fopen-fout retourneert het 1 als conservatieve 'mogelijk aanwezig'-uitkomst, niet exit/abort. Daarna probeert de bibliotheek mountdetectie. Deze uitleg past bij de gekoppelde bibliotheek en auditvolgorde; zonder syscalltrace is de precieze callsite niet individueel bewezen. De beperkte test vraagt geen SELinux-labels; Ubuntu gebruikt hier AppArmor.
Besluit: geen read-allow toevoegen. Deze denial kan bewust blijven bestaan zolang de test en de vereiste controles slagen. Minder auditruis is geen reden om de allowlist uit te breiden.

### /proc/25687/mounts — niet-fatale fallbackprobe
/proc/mounts verwijst naar /proc/self/mounts en verschijnt in audit als numerieke PID. libselinux init_selinuxmnt opent dit bij fallback; fopen-fout gaat naar out/return zonder procesafbreking. Dit is NIET hetzelfde als /proc/self/mountinfo dat Bubblewrap voor bindmountanalyse gebruikt. De kandidaat staat mountinfo al toe, maar mounts niet.
Besluit: geen /proc/mounts of numerieke mounts-read toevoegen. Verwachte niet-fatale probe; audit alleen bewijst geen aparte fatale mounttabelfout.

### capability sys_ptrace — waarschijnlijk niet-fatale namespace-ID-probe; niet vrijgeven
Bubblewrap namespace_ids_read(pid) doet fstatat op /proc/<child>/ns/... om namespace-inodes voor metadata te verzamelen. Derefereren wordt door Linux met ptrace-toegangschecks bewaakt en kan CAP_SYS_PTRACE raadplegen. De functie negeert een mislukte fstatat met continue. Het openen van de ns-directory zelf zou wel fataal zijn, maar die open-denial staat niet in deze audit. De sys_ptrace-denial op de monitor vóór mountopbouw past bij deze optionele metadataprobe; exacte oorzaak is zonder trace niet bewezen.
Besluit: capability sys_ptrace blijft afwezig (default deny). Geen nieuwe ptrace-allow of ruimere ns-files. Bestaande parent ptrace(read) peer=self wordt niet verruimd; de bestaande child-deny blijft identiek. Een algemene REQUIRED_CAPS-macro uit setuidcode bewijst geen noodzaak voor deze rootless /usr-only test. Als een volgende test een daadwerkelijk fatale syscall meldt, eerst callsite en errno onderzoeken, niet automatisch de capability toevoegen.

### /proc/25687/fd/ — niet-fataal, maar relevante FD-sanitatie
Bubblewrap utils.c fdwalk opent self/fd via openat(proc_fd,...). Bij open-fout retourneert deze implementatie res=0; er is dan GEEN numerieke FD-fallback. De numerieke lus verderop wordt alleen bereikt als de open lukte maar fdopendir faalt. Het eerdere idee dat elke fd-openfout automatisch wordt opgevangen door zo'n fallback zou onjuist zijn.
Bubblewrap gebruikt fdwalk met close_extra_fds in monitor_child en in het uiteindelijke exec-pad. Bij weigering kan dus opruimen van overgeërfde extra descriptors worden overgeslagen zonder fatale fout. Een geslaagde true is dan onvoldoende bewijs van veilige fd-hygiëne.
Besluit: alleen parentregel owner /proc/{self,@{pid}}/fd/ r toevoegen. Dit staat het opsommen van de directory toe, niet lezen/schrijven/uitvoeren van fd/* of readlink van targets. Geen disconnected fd-regel zolang daarvoor geen concrete noodzaak blijkt. owner + @{pid} kan dezelfde-UID-processen omvatten en is geen descendantfilter; kernel/DAC/ptracevoorwaarden blijven van toepassing. Geen nieuwe rechten in het kindprofiel. Deze toevoeging herstelt een veiligheidsrelevante routine, niet de fatale mountfout.

### mount / flags rw,silent,rslave — fatale blocker
Bubblewrap roept mount(NULL,"/",NULL,MS_SILENT|MS_SLAVE|MS_REC,NULL) aan vóór tmpfs/newroot-opbouw. Bij fout volgt die_with_mount_error; die functie eindigt met exit(1). Parent/monitor kan de status doorgeven; de oorspronkelijke gemeten exitcode blijft desondanks onbekend.
AppArmor gebruikt rslave voor MS_SLAVE|MS_REC en silent voor MS_SILENT. De bestaande options=(rw,rslave) matcht de geaudite combinatie met silent niet. rw is hier de weergave van de niet-gezetten MS_RDONLY-bit, geen algemene bestandswrite-toekenning. Silent onderdrukt bepaalde mountdiagnostiek, niet AppArmor-auditlogging. Het verwijderen van rslave uit de test zou mountpropagatiebescherming omzeilen; dat is geen passende reparatie.
Besluit: exacte optiecombinatie naar (rw,silent,rslave). Dezelfde bronversie zet MS_SILENT ook bij de twee bindsetupstappen, read-only bindremount en oldroot-rprivate; vier bijbehorende regels worden daarom eveneens exact gecorrigeerd. Geen brede mount-allow en geen options in met willekeurige subsets.

## Mountflags tegen broncode en AppArmor 4.0
1. Root slave: MS_SILENT|MS_SLAVE|MS_REC → rw,silent,rslave; audit bevestigt deze combinatie.
2. Newroot-bind: MS_SILENT|MS_BIND|MS_REC (plus legacy MS_MGC_VAL in bron) → rw,silent,rbind. Geen magic mountbits als AppArmor-optie toevoegen; die legacy waarde is geen extra toestemmingsklasse.
3. /usr-bind in bind-mount.c: MS_SILENT|MS_BIND|MS_REC → rw,silent,rbind met bestaande bron/doelpaden.
4. Read-only bindremount: MS_SILENT|MS_BIND|MS_REMOUNT|new_flags → ro,silent,remount,bind,nosuid,nodev,relatime voor de huidige root-/usr-mounttoestand. Geen ro/nosuid/nodev loslaten. Andere bronfilesystemflags of submounts blijven mogelijke toekomstige blockers.
5. Oldroot private: MS_SILENT|MS_REC|MS_PRIVATE → rw,silent,rprivate.
6. tmpfs- en proc-mounts hebben in de onderzochte bron geen MS_SILENT; die regels veranderen niet. Pivots/unmounts en alle bron-/doelpaden blijven gelijk.

De lokale AppArmor 4.0-manpage noemt silent/loud en exacte options-combinaties; parser/mount.cc v4.0.1 mappt silent op MS_SILENT en rslave op de recursieve slavebits. Compileracceptatie bewijst dat de syntax herkenbaar is, niet dat alle toekomstige mountgebeurtenissen passen.

## Exacte wijzigingen en kandidaatidentiteit
Bron: /home/mau/server5-commandcenter/config/apparmor/server5-bwrap.
Vorige kandidaat SHA256: f983a387e60eda7328bf9b0f96ed484e446dedb79c8aca11b3731a15e4e8a93a.
Nieuwe kandidaat SHA256: 9e84a1ab68b27c9ab0caefcccb03122819fc05e0edcd3c5f53a22cfb3e9978c2.
Volledige nieuwe inhoud staat ook in docs/apparmor-bwrap-voorstel.md. Hieronder de volledige profieldiff tegen de voorafgaande Git-versie:

```diff
diff --git a/config/apparmor/server5-bwrap b/config/apparmor/server5-bwrap
index 1ab21b3..e4880e4 100644
--- a/config/apparmor/server5-bwrap
+++ b/config/apparmor/server5-bwrap
@@ -21,6 +21,8 @@ profile server5-bwrap /usr/bin/bwrap flags=(attach_disconnected.path=/att/server
   /proc/sys/kernel/{overflowuid,overflowgid,cap_last_cap} r,
   /proc/sys/user/max_user_namespaces r,
   owner /proc/{self,@{pid}}/ r,
+  # Directory enumeration only, for fdwalk/close_extra_fds; no fd/* access.
+  owner /proc/{self,@{pid}}/fd/ r,
   owner /proc/{self,@{pid}}/{mountinfo,status,stat} r,
   owner /proc/{self,@{pid}}/attr/current r,
   owner /proc/{self,@{pid}}/ns/{user,mnt,pid,cgroup} r,
@@ -42,14 +44,14 @@ profile server5-bwrap /usr/bin/bwrap flags=(attach_disconnected.path=/att/server
   /oldroot/usr/ r,

   # bwrap 0.9.0 setup sequence, restricted by operation/source/destination.
-  mount options=(rw,rslave) -> /,
+  mount options=(rw,silent,rslave) -> /,
   mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /tmp/,
-  mount options=(rw,rbind) /tmp/newroot/ -> /tmp/newroot/,
+  mount options=(rw,silent,rbind) /tmp/newroot/ -> /tmp/newroot/,
   pivot_root oldroot=/tmp/oldroot/ /tmp/,
-  mount options=(rw,rbind) /oldroot/usr/ -> /newroot/usr/,
-  mount options=(ro,remount,bind,nosuid,nodev,relatime) -> /newroot/usr/,
+  mount options=(rw,silent,rbind) /oldroot/usr/ -> /newroot/usr/,
+  mount options=(ro,silent,remount,bind,nosuid,nodev,relatime) -> /newroot/usr/,
   mount fstype=proc options=(rw,nosuid,nodev,noexec) proc -> /newroot/proc/,
-  mount options=(rw,rprivate) -> /oldroot/,
+  mount options=(rw,silent,rprivate) -> /oldroot/,
   umount /oldroot/,
   pivot_root oldroot=/newroot/ /newroot/,
   umount /,
```

De enige nieuwe bestandsmachtiging is fd-directory-read in de parent. Vijf mountregels eisen aanvullend silent; het is een preciezere vereiste combinatie, geen willekeurige extra mountoperatie. Parentcapabilities blijven exact setpcap en sys_admin. Geen /proc/filesystems-, mounts-, sys_ptrace-, home-, netwerk-, shell- of algemene fd-targettoegang toegevoegd. Het volledige kindprofiel blijft bytegelijk.

## Offline validatie en security-review
Verplicht en in deze ronde uitgevoerd als mau, zonder sudo:

```bash
apparmor_parser --skip-kernel-load --skip-cache --Werror \
  -I /etc/apparmor.d \
  /home/mau/server5-commandcenter/config/apparmor/server5-bwrap
```

Exit 0 zonder waarschuwingen. Git-diff --check en gerichte contractcontrole: alleen bedoelde fd-read en vijf silent-correcties, capabilities identiek, child bytegelijk, geen globale allow/complain/unconfined of nieuwe execfallbacks. Kandidatenhash en ingevoegde volledige reviewinhoud gecontroleerd. Geen policy geladen, geen bestanden onder /etc gewijzigd en geen sysctl, netwerk, SSH of sudoers aangepast.

Resterende risico's: disconnected-prefixaliasing; parent-capability sys_admin is gevoelig; owner-PIDpatronen omvatten meer dan één proces; mountpaden/flags en stacked exec kunnen verderop nog falen. De fd-directoryregel helpt sanitatie, maar bewijst geen volledige fd-isolatie. Een werkende true bewijst geen Codex-, shell- of netwerkisoleringsgeschiktheid. Geen productie- of veiligheidsacceptatie totdat positieve/negatieve controles en de echte exitstatus beschikbaar zijn.

## Volgende beperkte runtimeproef — NIET NU UITVOEREN
Deze procedure vereist ChatGPT-review en nieuwe expliciete toestemming. De profielen blijven nu verwijderd. Alleen één /usr-only true-proef na een tijdelijke load van exact R2; geen herhaalde automatische profielverbreding. Geen oude prepare-security.sh of algemene bwrap-installatieprocedure opnieuw uitvoeren.

1. Beheerder verifieert met bestaande sudo-rechten dat beide profielnamen weg zijn, er geen conflicterend /usr/bin/bwrap-attachment bestaat, eigen testprocessen gestopt zijn en /att/server5-bwrap afwezig is. Controleer de werkelijk geladen profielnamen; een sudo-fout is geen bewijs van afwezigheid.
2. Gebruik een NIEUWE root-owned locatie /root/server5-apparmor-review-r2/server5-bwrap. Bewaar de vorige proefkopie. Als de R2-locatie bestaat: stop en beoordeel; niet overschrijven. Kopieer de kandidaat als root-owned 0600, verifieer bovenstaande nieuwe SHA256 en voer daar opnieuw -Q -K --Werror uit.
3. Pas na controle en toestemming tijdelijk laden met --add --skip-cache, geen --replace of globale reload en geen /etc-installatie. Verifieer beide namen in enforce. Laat LAN-SSH open. De precieze eerdere rollback blijft gericht op deze nieuwe rootkopie.
4. Voer als mau de volgende ene proef uit, niet via sudo bwrap. Dit is een voorgestelde terminalprocedure, geen nieuw geïnstalleerd uitvoeringsscript. Bewaar commandoregel, stderr en status direct, zonder pipeline. --unshare-cgroup-try is gelijk aan de eerder gedocumenteerde proef; de commandoregel van de feitelijke eerste proef is onbekend en moet indien beschikbaar apart worden toegevoegd.

```bash
trial_dir="$(mktemp -d /home/mau/server5-commandcenter/inventory/bwrap-r2.XXXXXX)"
date -u --iso-8601=seconds > "$trial_dir/start-utc.txt"
sha256sum /home/mau/server5-commandcenter/config/apparmor/server5-bwrap > "$trial_dir/profile-sha256.txt"
smoke_cmd=(/usr/bin/bwrap --unshare-user --unshare-pid --unshare-cgroup-try
  --die-with-parent --clearenv --chdir /
  --ro-bind /usr /usr
  --symlink usr/bin /bin --symlink usr/lib /lib
  --symlink usr/lib64 /lib64 --proc /proc --dir /tmp
  /usr/bin/true)
printf '%q ' "${smoke_cmd[@]}" > "$trial_dir/command.txt"
printf '\n' >> "$trial_dir/command.txt"
if "${smoke_cmd[@]}" > "$trial_dir/stdout.txt" 2> "$trial_dir/stderr.txt"; then
  trial_rc=0
else
  trial_rc=$?
fi
printf '%s\n' "$trial_rc" > "$trial_dir/exit-status.txt"
date -u --iso-8601=seconds > "$trial_dir/end-utc.txt"
printf 'Proefmap: %s; exitcode: %s\n' "$trial_dir" "$trial_rc"
```

5. Beheerder bewaart audit tussen start/einde plus een kleine marge; koppel pid/comm/label aan deze ene proef. Bij niet-nul: behoud stderr en stop vóór verdere payloadtests. Geen allow-regels toevoegen op basis van alle DENIED samen. Bij nul: resultaat is slechts true-smoke; daarna stoppen voor review. Verdere cat-/sleep-, stack-, capability- en fd-lektests vragen een volgende gecontroleerde teststap.
6. Bekende filesystems/mounts/sys_ptrace-probes mogen audit blijven geven mits de callsite niet-fataal blijkt en geen vereiste stap faalt. Een fd-directorydenial blijft een reviewstop voor sanitatie, ook bij exit 0. Onverwachte denial, verkeerde labels, behoud van bruikbare privileges of onduidelijke status → geen vrijgave.
7. Ruim na de proef alleen eigen testprocessen op en verwijder beide tijdelijke profielen uit de kernel; bewaar de rootkopie en alle bewijs. Geen console-/SSH-/netwerkreset. Definitieve kernelafwezigheid door beheerder bevestigen.

## Rollback — voorbereid, nu niet uitvoeren
Nu alleen lokale bestanden aangepast: gericht Git-revert van deze reviewcommit herstelt de vorige kandidaat; geen profielunload nodig op grond van een door ons uitgevoerde load. Niet het eerder al verwijderde profiel opnieuw laden als rollback.

Na een later expliciet toegestane R2-proef: stop uitsluitend eigen testprocessen en gebruik de ongewijzigde R2-rootkopie:

```bash
sudo apparmor_parser --remove --skip-cache -I /etc/apparmor.d \
  /root/server5-apparmor-review-r2/server5-bwrap
sudo cat /sys/kernel/security/apparmor/profiles
```

Beide namen moeten ontbreken. Als alleen één profiel geladen is, geen globale AppArmor-reload; beheerder verwijdert alleen het aanwezige nieuwe profiel gericht. Geen bestaand /etc-bestand terugzetten, geen sysctl of andere dienst aanpassen. Rootkopie en logs behouden. Dit is terug naar eerdere beveiligingsstatus, niet een sandboxfix.

## Documentatie en stopstatus
2026-10-21: uitsluitend lokaal kandidaatprofiel en bijbehorende reviewdocumentatie gewijzigd. Reden: vijf specifieke denials causaal beoordelen zonder capabilities blind vrij te geven. Geen uitvoeringstoestemming afgeleid uit 'verder gaan': dat betekent deze review afronden. Git/Notion/MindMap vastleggen en STOP voor ChatGPT-review en nieuwe toestemming. M0 blijft open, geen netwerk-/webuitrol.

## Primaire bronnen
- Bubblewrap 0.9.0 namespace_ids_read en mount/failurepad: https://raw.githubusercontent.com/containers/bubblewrap/v0.9.0/bubblewrap.c
- fdwalk: https://raw.githubusercontent.com/containers/bubblewrap/v0.9.0/utils.c
- Bind/remountflags: https://raw.githubusercontent.com/containers/bubblewrap/v0.9.0/bind-mount.c
- SELinux 3.5 detectieconstructor: https://raw.githubusercontent.com/SELinuxProject/selinux/3.5/libselinux/src/init.c
- AppArmor 4.0.1 flagmapping: https://gitlab.com/apparmor/apparmor/-/raw/v4.0.1/parser/mount.cc
- Lokale distributiemanpage /usr/share/man/man5/apparmor.d.5.gz en journalctl-audit 2026-10-21 06:35:02. De originele stderr/exitcode blijven ontbrekend.
