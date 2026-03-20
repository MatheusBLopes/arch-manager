"""
Geração de PDF com todo o conteúdo do sistema.
Utiliza ReportLab (puro Python, sem dependências de sistema).
"""
import io
import json
import re
from html import escape

import markdown
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.flowables import Flowable

from arch_manager.apps.docs.models import ResourceDocumentation
from arch_manager.apps.projects.models import Project, ProjectDocumentation
from arch_manager.apps.relationships.models import ResourceRelationship
from arch_manager.apps.resources.models import (
    ApiGatewayEndpoint,
    ApiGatewayEndpointMethod,
    ApiGatewayExampleCurl,
    ApiGatewayInvocation,
    ApiGatewayParameter,
    ApiGatewayPayload,
    DatabaseQuery,
    DatabaseTable,
    Resource,
    TableField,
    TableRelationship,
)


class SectionFlowable(Flowable):
    """Flowable que marca início de seção para o sumário."""

    def __init__(self, level, title, key):
        super().__init__()
        self.level = level
        self.title = title
        self.key = key

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        pass


class HorizontalLineFlowable(Flowable):
    """Flowable que desenha uma linha horizontal separadora."""

    def __init__(self, line_width=1, color=None, space_before=0.4, space_after=0.4):
        super().__init__()
        self.line_width = line_width
        self.color = color or colors.HexColor("#999999")
        self.space_before = space_before * cm
        self.space_after = space_after * cm
        self._draw_width = 0

    def wrap(self, availWidth, availHeight):
        self._draw_width = availWidth
        return (availWidth, self.space_before + self.line_width + self.space_after)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.line_width)
        y = self.space_after + self.line_width / 2
        self.canv.line(0, y, self._draw_width, y)


# Cor de fundo para blocos JSON/SQL
_CODE_BLOCK_BG = colors.HexColor("#e8f4fc")
_MAX_LINE_LEN = 100


def _format_json(text):
    """Tenta formatar texto como JSON com indentação."""
    text = (text or "").strip()
    if not text:
        return text
    try:
        obj = json.loads(text)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return text


def _format_sql(text):
    """Adiciona quebras de linha antes de palavras-chave SQL para legibilidade."""
    text = (text or "").strip()
    if not text:
        return text
    # Insere quebra antes de palavras-chave (case insensitive)
    keywords = r"\b(SELECT|FROM|WHERE|AND|OR|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|INSERT INTO|VALUES|UPDATE|SET|DELETE)\b"
    return re.sub(keywords, r"\n\1", text, flags=re.IGNORECASE).strip()


def _break_long_lines(text, max_len=_MAX_LINE_LEN):
    """Quebra linhas longas preservando palavras quando possível."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if len(line) <= max_len:
            result.append(line)
            continue
        pos = 0
        while pos < len(line):
            chunk = line[pos : pos + max_len]
            # Tenta quebrar em espaço/virgula/ponto-e-vírgula
            if pos + max_len < len(line):
                break_at = max(
                    chunk.rfind(" "),
                    chunk.rfind(","),
                    chunk.rfind(";"),
                    chunk.rfind("("),
                    chunk.rfind(")"),
                )
                if break_at > max_len // 2:
                    chunk = chunk[: break_at + 1]
                    pos += break_at + 1
                else:
                    pos += max_len
            else:
                pos = len(line)
            result.append(chunk)
    return "\n".join(result)


def _code_text_to_paragraph(text, max_len=_MAX_LINE_LEN):
    """Converte texto de código para string formatada para Paragraph (escape + <br/>)."""
    # Preserva espaços iniciais com caractere Unicode de espaço não-quebrável
    _NBSP = "\u00A0"

    def preserve_indent(s):
        count = len(s) - len(s.lstrip(" "))
        return _NBSP * count + s[count:] if count else s

    lines = text.split("\n")
    escaped = [escape(preserve_indent(line)) for line in lines]
    return "<br/>".join(escaped)


class CodeBlockFlowable(Flowable):
    """
    Bloco de código (JSON/SQL) com fundo azulado, quebra de linha automática
    e formatação para legibilidade.
    """

    def __init__(self, text, format_type, base_style):
        super().__init__()
        self.text = (text or "").strip()
        self.format_type = format_type
        self.base_style = base_style
        self._table = None

    def _prepare(self, availWidth):
        if not self.text:
            return 0, 0
        text = self.text
        if self.format_type == "json":
            text = _format_json(text)
        elif self.format_type == "sql":
            text = _format_sql(text)
        text = _break_long_lines(text, _MAX_LINE_LEN)
        para_text = _code_text_to_paragraph(text)

        # Estilo base com Courier
        style = ParagraphStyle(
            name="CodeBlock",
            parent=self.base_style,
            fontName="Courier",
            fontSize=8,
            borderPadding=2,
            spaceBefore=0,
            spaceAfter=0,
            leftIndent=0,
        )
        para = Paragraph(f'<font name="Courier" size="8">{para_text}</font>', style)
        self._table = Table([[para]], colWidths=[max(availWidth - 16, 100)])
        self._table.setStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _CODE_BLOCK_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaccdd")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
        w, h = self._table.wrap(availWidth, 9999)
        return w, h

    def wrap(self, availWidth, availHeight):
        if not self.text:
            return (0, 0)
        self._prepare(availWidth)
        return self._table.wrap(availWidth, availHeight)

    def draw(self):
        if self.text and self._table:
            self._table.drawOn(self.canv, 0, 0)


def _make_code_block(text, format_type, style):
    """Cria flowable para bloco JSON/SQL com fundo azulado e formatação."""
    if not (text or "").strip():
        return Spacer(1, 0)
    return CodeBlockFlowable(text, format_type, style)


def _html_to_reportlab_inline(container):
    """
    Converte elemento HTML para string com tags ReportLab (b, i, font, br).
    ReportLab Paragraph suporta: b, i, u, br, font (name, size, color), sub, super, strike.
    """
    if container is None:
        return ""
    try:
        children = container.children
    except AttributeError:
        return escape(str(container))
    parts = []
    for child in children:
        if not hasattr(child, "name"):
            parts.append(escape(str(child)))
            continue
        if child.name in ("strong", "b"):
            parts.append(f"<b>{_html_to_reportlab_inline(child)}</b>")
        elif child.name in ("em", "i"):
            parts.append(f"<i>{_html_to_reportlab_inline(child)}</i>")
        elif child.name == "code":
            parts.append(f'<font name="Courier">{_html_to_reportlab_inline(child)}</font>')
        elif child.name == "a":
            parts.append(f'<font color="#2266aa">{_html_to_reportlab_inline(child)}</font>')
        elif child.name == "br":
            parts.append("<br/>")
        elif child.name in ("span", "div"):
            parts.append(_html_to_reportlab_inline(child))
        else:
            parts.append(_html_to_reportlab_inline(child))
    return "".join(parts)


def _iter_block_elements(soup, block_tags):
    """Itera sobre elementos de bloco na ordem do documento (apenas top-level)."""
    for child in soup.children:
        if not hasattr(child, "name"):
            continue
        if child.name in block_tags:
            yield child
        elif child.name in ("div", "section", "body", "html"):
            yield from _iter_block_elements(child, block_tags)


def _markdown_to_flowables(text, styles, code_style):
    """
    Converte Markdown para lista de flowables ReportLab, respeitando estrutura e formatação.
    styles: dict com h1_style, h2_style, h3_style, body_style
    """
    if not (text or "").strip():
        return []
    html = markdown.markdown(
        text,
        extensions=["extra", "codehilite", "nl2br"],
        extension_configs={"codehilite": {"css_class": "highlight"}},
    )
    soup = BeautifulSoup(html, "html.parser")
    flowables = []
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "blockquote", "hr"]
    heading_styles = {
        "h1": styles.get("h1_style") or styles["body_style"],
        "h2": styles.get("h2_style") or styles["body_style"],
        "h3": styles.get("h3_style") or styles["body_style"],
        "h4": styles.get("h3_style") or styles["body_style"],
        "h5": styles.get("h3_style") or styles["body_style"],
        "h6": styles.get("h3_style") or styles["body_style"],
    }
    body = styles["body_style"]

    for elem in _iter_block_elements(soup, block_tags):
        if elem.name in heading_styles:
            content = _html_to_reportlab_inline(elem)
            if content.strip():
                flowables.append(Paragraph(content, heading_styles[elem.name]))
        elif elem.name == "p":
            content = _html_to_reportlab_inline(elem)
            if content.strip():
                flowables.append(Paragraph(content, body))
        elif elem.name == "pre":
            code = elem.find("code")
            raw = code.get_text() if code else elem.get_text()
            if raw.strip():
                flowables.append(_make_code_block(raw, "other", code_style))
        elif elem.name in ("ul", "ol"):
            for i, li in enumerate(elem.find_all("li", recursive=False)):
                content = _html_to_reportlab_inline(li)
                if content.strip():
                    bullet = "•" if elem.name == "ul" else f"{i + 1}."
                    flowables.append(Paragraph(f"{bullet} {content}", body))
        elif elem.name == "blockquote":
            content = _html_to_reportlab_inline(elem)
            if content.strip():
                flowables.append(Paragraph(f'<i>{content}</i>', body))
        elif elem.name == "hr":
            flowables.append(HorizontalLineFlowable(
                line_width=0.5,
                color=colors.HexColor("#cccccc"),
                space_before=0.3,
                space_after=0.3,
            ))

    if not flowables and soup.get_text(strip=True):
        flowables.append(Paragraph(escape(soup.get_text()), body))

    return flowables


def _project_for_page(doc, page_num):
    """Retorna o nome do projeto/sessão para a página atual."""
    sections = getattr(doc, "_page_sections", [])
    best = None
    for p, s in sections:
        if p <= page_num:
            best = s
    if best is not None:
        return best
    if page_num == 1:
        return "Arch Manager"
    if page_num == 2:
        return "Sumário"
    return ""


class ArchDocTemplate(SimpleDocTemplate):
    """Template que registra seções no sumário e projetos por página."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toc = None
        self._page_sections = []

    def set_toc(self, toc):
        self._toc = toc

    def afterFlowable(self, flowable):
        if isinstance(flowable, SectionFlowable):
            page_num = self.canv.getPageNumber()
            if self._toc:
                self.canv.bookmarkPage(flowable.key)
                self.notify("TOCEntry", (flowable.level, flowable.title, page_num, flowable.key))
            # level 0 = projeto ou "Outros"
            if flowable.level == 0:
                self._page_sections.append((page_num, flowable.title))

    def afterPage(self):
        """Desenha o cabeçalho com o nome do projeto ao final de cada página."""
        if not getattr(self, "canv", None):
            return
        self.canv.saveState()
        page_num = self.canv.getPageNumber()
        project_name = _project_for_page(self, page_num)
        if project_name:
            self.canv.setFont("Helvetica", 9)
            self.canv.setFillColor(colors.HexColor("#666666"))
            page_height = self.pagesize[1]
            y = page_height - 0.6 * cm
            self.canv.drawString(self.leftMargin, y, project_name)
        self.canv.restoreState()


def build_pdf_buffer():
    """Constrói o PDF e retorna um buffer de bytes."""
    buffer = io.BytesIO()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=30,
    )
    h1_style = ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=14,
        spaceAfter=6,
    )
    h3_style = ParagraphStyle(
        name="H3",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
    )
    code_style = ParagraphStyle(
        name="Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=9,
        backColor=colors.HexColor("#f5f5f5"),
        borderPadding=4,
        spaceAfter=6,
    )
    section_header_style = ParagraphStyle(
        name="SectionHeader",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        backColor=colors.HexColor("#e8e8e8"),
        borderPadding=6,
        spaceBefore=0,
        spaceAfter=6,
        textColor=colors.HexColor("#333333"),
    )
    label_style = ParagraphStyle(
        name="Label",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#444444"),
        spaceAfter=2,
    )
    value_style = ParagraphStyle(
        name="Value",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=12,
        spaceAfter=4,
    )
    thin_separator = HorizontalLineFlowable(
        line_width=0.25,
        color=colors.HexColor("#dddddd"),
        space_before=0.2,
        space_after=0.2,
    )

    doc = ArchDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
    )

    toc = TableOfContents(dotsMinLevel=0)
    doc.set_toc(toc)

    story = []

    # Capa
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Arch Manager", title_style))
    story.append(Paragraph("Documentação Completa do Sistema", body_style))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "Este documento contém toda a documentação de projetos, recursos e suas relações.",
        body_style,
    ))
    story.append(PageBreak())

    # Sumário
    story.append(Paragraph("Sumário", h1_style))
    story.append(toc)
    story.append(PageBreak())

    seq = [0]

    def _key():
        seq[0] += 1
        return f"s{seq[0]}"

    # Linhas separadoras (projetos: mais grossa/escura; recursos: mais fina/clara)
    project_line = HorizontalLineFlowable(
        line_width=2,
        color=colors.HexColor("#555555"),
        space_before=0.6,
        space_after=0.6,
    )
    resource_line = HorizontalLineFlowable(
        line_width=0.5,
        color=colors.HexColor("#cccccc"),
        space_before=0.3,
        space_after=0.3,
    )

    # Projetos
    projects = Project.objects.prefetch_related("resources__resource_type").order_by("name")
    for idx, project in enumerate(projects):
        if idx > 0:
            story.append(project_line)
        story.append(SectionFlowable(0, project.name, _key()))
        story.append(Paragraph(escape(project.name), h1_style))
        story.append(Paragraph(f'<b>Descrição:</b> {escape(project.short_description)}', body_style))

        # Documentação do projeto
        try:
            proj_doc = project.documentation
            if proj_doc and proj_doc.markdown_content:
                story.append(Spacer(1, 0.5 * cm))
                story.append(Paragraph(escape(proj_doc.title), h2_style))
                md_styles = {
                    "h1_style": h1_style,
                    "h2_style": h2_style,
                    "h3_style": h3_style,
                    "body_style": body_style,
                }
                story.extend(_markdown_to_flowables(proj_doc.markdown_content, md_styles, code_style))
        except ProjectDocumentation.DoesNotExist:
            pass

        # Recursos do projeto
        resources = project.resources.select_related("resource_type", "lambda_details").prefetch_related(
            "documentation",
            "outgoing_relationships__target_resource",
            "incoming_relationships__source_resource",
            "database_tables__fields",
            "api_endpoints__methods",
        ).order_by("name")

        for res_idx, resource in enumerate(resources):
            if res_idx > 0:
                story.append(resource_line)
            story.append(SectionFlowable(1, resource.name, _key()))
            _add_resource_content(
                story, resource,
                h2_style, h3_style, body_style, code_style,
                section_header_style, label_style, value_style, thin_separator,
            )

        story.append(Spacer(1, 1 * cm))

    # Outros (recursos sem projeto)
    others = Resource.objects.filter(project__isnull=True).select_related("resource_type", "lambda_details").prefetch_related(
        "documentation",
        "outgoing_relationships__target_resource",
        "incoming_relationships__source_resource",
        "database_tables__fields",
        "api_endpoints__methods",
    ).order_by("name")

    if others.exists():
        story.append(project_line)
        story.append(SectionFlowable(0, "Outros", _key()))
        story.append(Paragraph("Outros (recursos sem projeto)", h1_style))
        story.append(Paragraph(
            "Recursos que não estão vinculados a nenhum projeto.",
            body_style,
        ))
        story.append(Spacer(1, 0.5 * cm))

        for res_idx, resource in enumerate(others):
            if res_idx > 0:
                story.append(resource_line)
            story.append(SectionFlowable(1, resource.name, _key()))
            _add_resource_content(
                story, resource,
                h2_style, h3_style, body_style, code_style,
                section_header_style, label_style, value_style, thin_separator,
            )

    doc.multiBuild(story)
    buffer.seek(0)
    return buffer.getvalue()


def _add_resource_content(
    story, resource,
    h2_style, h3_style, body_style, code_style,
    section_header_style, label_style, value_style, thin_separator,
):
    """Adiciona conteúdo completo de um recurso ao story."""
    # Cabeçalho do recurso
    story.append(Paragraph(escape(resource.name), h2_style))
    story.append(Paragraph(
        f'<b>Tipo:</b> <font color="#2266aa">{escape(resource.resource_type.name)}</font>',
        body_style,
    ))
    story.append(Paragraph(
        f'<b>Descrição:</b> <i>{escape(resource.short_description)}</i>',
        body_style,
    ))
    if resource.detailed_description:
        story.append(Paragraph(
            f'<b>Descrição detalhada:</b> {escape(resource.detailed_description)}',
            value_style,
        ))

    ld = resource.get_lambda_details()

    # Metadados
    meta_items = []
    if ld and ld.runtime_version:
        meta_items.append(("Runtime", ld.runtime_version))
    if resource.repository_url:
        meta_items.append(("Repositório", resource.repository_url))
    if resource.has_pentest:
        meta_items.append(("Pentest", "Sim"))
    if resource.notes:
        meta_items.append(("Notas", resource.notes))
    if meta_items:
        story.append(thin_separator)
        story.append(Paragraph("Metadados", section_header_style))
        for label, val in meta_items:
            story.append(Paragraph(
                f'<b>{escape(label)}:</b> {escape(str(val))}',
                value_style,
            ))

    # Documentação
    try:
        doc = resource.documentation
        if doc and doc.markdown_content:
            story.append(thin_separator)
            story.append(Paragraph(escape(doc.title), section_header_style))
            md_styles = {
                "h1_style": h2_style,
                "h2_style": h3_style,
                "h3_style": value_style,
                "body_style": value_style,
            }
            story.extend(_markdown_to_flowables(doc.markdown_content, md_styles, code_style))
    except ResourceDocumentation.DoesNotExist:
        pass

    # Lambda (detalhes específicos)
    if resource.is_lambda() and ld:
        if ld.example_invocation_payload or ld.mermaid_diagram:
            story.append(thin_separator)
            story.append(Paragraph("Detalhes Lambda", section_header_style))
            if ld.example_invocation_payload:
                story.append(Paragraph('<b>Payload de exemplo:</b>', label_style))
                story.append(_make_code_block(ld.example_invocation_payload, "json", code_style))
            if ld.mermaid_diagram:
                story.append(Paragraph('<b>Diagrama de processo:</b>', label_style))
                story.append(_make_code_block(ld.mermaid_diagram, "other", code_style))

    # Relacionamentos
    outgoing = resource.outgoing_relationships.filter(is_active=True).select_related("target_resource")
    incoming = resource.incoming_relationships.filter(is_active=True).select_related("source_resource")
    if outgoing.exists() or incoming.exists():
        story.append(thin_separator)
        story.append(Paragraph("Relacionamentos", section_header_style))
        if outgoing.exists():
            story.append(Paragraph('<b>Sai para:</b>', label_style))
            for rel in outgoing:
                story.append(Paragraph(
                    f'→ <font color="#2266aa">{escape(rel.target_resource.name)}</font> '
                    f'<i>({escape(rel.get_relationship_type_display())})</i>',
                    value_style,
                ))
        if incoming.exists():
            story.append(Paragraph('<b>Recebe de:</b>', label_style))
            for rel in incoming:
                story.append(Paragraph(
                    f'← <font color="#2266aa">{escape(rel.source_resource.name)}</font> '
                    f'<i>({escape(rel.get_relationship_type_display())})</i>',
                    value_style,
                ))

    # Banco de dados (tabelas, campos, queries)
    if resource.is_database():
        tables = DatabaseTable.objects.filter(resource=resource).prefetch_related(
            "fields", "outgoing_relations", "incoming_relations"
        )
        if tables.exists():
            story.append(thin_separator)
            story.append(Paragraph("Schema do Banco", section_header_style))
            for table in tables:
                story.append(Paragraph(
                    f'<b>Tabela:</b> <font color="#228844">{escape(table.name)}</font>',
                    label_style,
                ))
                if table.description:
                    story.append(Paragraph(f'<i>{escape(table.description)}</i>', value_style))
                fields = list(table.fields.all())
                if fields:
                    header_style = ParagraphStyle(
                        name="TableHeader",
                        parent=body_style,
                        fontName="Helvetica-Bold",
                        backColor=colors.HexColor("#d0e0f0"),
                        borderPadding=4,
                    )
                    data = [
                        [
                            Paragraph("Nome", header_style),
                            Paragraph("Tipo", header_style),
                            Paragraph("PK", header_style),
                            Paragraph("Nullable", header_style),
                            Paragraph("Descrição", header_style),
                        ]
                    ]
                    for field in fields:
                        data.append([
                            Paragraph(f'<font name="Courier">{escape(field.name)}</font>', value_style),
                            Paragraph(f'<font name="Courier">{escape(field.data_type or "—")}</font>', value_style),
                            Paragraph("Sim" if field.is_primary_key else "—", value_style),
                            Paragraph("Sim" if field.is_nullable else "Não", value_style),
                            Paragraph(escape((field.description or "")[:50] + ("..." if len(field.description or "") > 50 else "")), value_style),
                        ])
                    tbl = Table(data, colWidths=[80, 80, 35, 45, "*"])
                    tbl.setStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d0e0f0")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaccdd")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ])
                    story.append(tbl)
                    story.append(Spacer(1, 0.3 * cm))
            queries = DatabaseQuery.objects.filter(resource=resource)
            for q in queries:
                story.append(Paragraph(f'<b>Query:</b> {escape(q.name)}', label_style))
                if q.description:
                    story.append(Paragraph(f'<i>{escape(q.description)}</i>', value_style))
                story.append(_make_code_block(q.query_text, "sql", code_style))

    # API Gateway (endpoints, métodos, parâmetros, payloads, invocações, curls)
    if resource.is_api_gateway():
        endpoints = ApiGatewayEndpoint.objects.filter(resource=resource).prefetch_related(
            "methods__parameters",
            "methods__payloads",
            "methods__invocations__target_resource",
            "methods__example_curls",
        )
        if endpoints.exists():
            story.append(thin_separator)
            story.append(Paragraph("Endpoints da API", section_header_style))
            for ep in endpoints:
                story.append(Paragraph(
                    f'<b>Path:</b> <font name="Courier" color="#aa2266">{escape(ep.path)}</font>',
                    label_style,
                ))
                if ep.description:
                    story.append(Paragraph(f'<i>{escape(ep.description)}</i>', value_style))
                for method in ep.methods.all():
                    story.append(Paragraph(
                        f'<b>{method.http_method}</b>',
                        label_style,
                    ))
                    if method.description:
                        story.append(Paragraph(f'<i>{escape(method.description)}</i>', value_style))
                    for p in method.parameters.all():
                        story.append(Paragraph(
                            f'  Parâmetro <b>{escape(p.name)}</b> ({p.get_param_in_display()}): '
                            f'<font name="Courier">{p.param_type or "—"}</font>',
                            value_style,
                        ))
                    for pl in method.payloads.all():
                        story.append(Paragraph(
                            f'  Payload {pl.get_direction_display()}: <i>{pl.content_type}</i>',
                            value_style,
                        ))
                        if pl.body:
                            body_text = pl.body[:500] + ("..." if len(pl.body) > 500 else "")
                            fmt = "json" if pl.content_type and "json" in pl.content_type.lower() else "other"
                            story.append(_make_code_block(body_text, fmt, code_style))
                    for inv in method.invocations.all():
                        story.append(Paragraph(
                            f'  Invoca: <font color="#2266aa">{escape(inv.target_resource.name)}</font>',
                            value_style,
                        ))
                    for curl in method.example_curls.all():
                        story.append(Paragraph(f'  Exemplo: <b>{escape(curl.label)}</b>', value_style))
                        story.append(_make_code_block(curl.curl_command, "other", code_style))

    story.append(Spacer(1, 0.3 * cm))
