# Terminal Clash – Street Fighter-inspirerat Androidspel

Projektets källkod finns ännu inte i detta repository. Android-workflowen kan därför inte skapa någon APK ännu.

## Lägg in spelet
1. Ladda ner `terminal_clash_v08_godot.zip` från ChatGPT-konversationen.
2. Packa upp ZIP-filen.
3. Öppna repositoryt på GitHub och välj **Add file → Upload files**.
4. Ladda upp innehållet i den uppackade mappen, **inte ZIP-filen som en enda fil**. Behåll mapparna `assets/` och `.github/workflows/`.
5. Bekräfta med **Commit changes**.

När filerna har lagts in på huvudgrenen kan GitHub Actions köra Android-bygget. Ett lyckat bygge ger en nedladdningsbar APK under workflow-körningens **Artifacts**.

**Observera:** Exporten är ännu inte verifierad; byggfel kan behöva rättas.
