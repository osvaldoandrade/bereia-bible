# Guardrails teológico-exegéticos — Bereia Version

Versão: **1.0.0** · Status: ATIVA

## 1. Hierarquia inegociável

1. O texto hebraico/aramaico/grego decide. Sempre.
2. Perspectiva cristã conservadora e reformada é **contexto exegético**, nunca
   autoridade textual.
3. Quando léxico + morfologia + sintaxe determinam a tradução, teologia não vota.
4. Quando existem duas ou mais traduções **semanticamente equivalentes e
   lexicalmente plenas**, coerência com a teologia bíblica e a leitura reformada
   pode desempatar — e o desempate é registrado como decisão, com as alternativas.
5. Quando o original é ambíguo entre posições teológicas, a BV **preserva a
   ambiguidade** e o registro documenta as leituras.

## 2. Proibições

- Harmonização artificial entre passagens paralelas (traduzir Gn 1 para "combinar"
  com Jo 1, ou sinóticos entre si).
- Importar exegese para dentro do texto (expansões interpretativas viram nota, não texto).
- Suavizar dificuldades do original (antropomorfismos, imprecatórios, tensões).
- Escolher glosa sem suporte lexical porque "soa mais ortodoxa".
- Apagar ou inserir implicação cristológica que o texto-fonte não codifica.

## 3. Teste de refutação (aplicado pelo Agente 4)

Para cada escolha disputada, perguntar:
1. Um tradutor judeu, um católico e um pentecostal competentes chegariam a esta
   tradução só com a gramática? Se não, qual evidência textual a sustenta?
2. A escolha sobrevive ao uso do mesmo lexema no restante do livro/corpus?
3. A escolha depende de uma doutrina para ser plausível? → NO-GO, voltar ao neutro.

## 4. Casos paradigmáticos (jurisprudência inicial)

- **Gn 1:2 רוּחַ אֱלֹהִים**: "Espírito de Deus" e "vento de Deus" são ambos
  lexicalmente possíveis; a decisão e a leitura alternativa DEVEM constar do registro.
- **Is 7:14 עַלְמָה**: traduzir pelo valor lexical ("jovem"/"virgem" conforme
  evidência), registrar o uso em Mt 1:23 na justificativa — não retroprojetar.
- **Textos de eleição/soberania (Rm 9, Ef 1)**: traduzir a sintaxe como está;
  a leitura reformada não precisa de ajuda da tradução.
- **Variantes com peso doutrinário (Jo 1:18; 1Tm 3:16)**: seguir a evidência
  textual da fonte pinada; variante relevante vai para `variantes_textuais`.

## 5. Confissão de viés

Todo registro em que o desempate reformado foi usado deve dizê-lo explicitamente
no campo `decisoes[].justificativa` com a fórmula: "desempate por coerência
teológica entre equivalentes plenos" — para que auditores localizem todos esses
pontos com `grep`.
