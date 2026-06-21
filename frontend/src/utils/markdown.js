/**
 * Safe, zero-dependency Markdown parser.
 * Escapes input HTML first to prevent XSS, then maps basic markdown constructs.
 */
export function parseMarkdown(text) {
  if (!text) return "";
  
  // Escape HTML tags to prevent XSS
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Replace bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Replace italic: *text*
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
  
  // Replace code tags: `code`
  html = html.replace(/`(.*?)`/g, "<code>$1</code>");
  
  // Parse lines for paragraph block construction & lists
  const lines = html.split("\n");
  const result = [];
  let inUnorderedList = false;
  let inOrderedList = false;
  
  for (let line of lines) {
    const trimmed = line.trim();
    
    // Unordered lists
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      if (inOrderedList) {
        result.push("</ol>");
        inOrderedList = false;
      }
      if (!inUnorderedList) {
        result.push('<ul class="md-ul">');
        inUnorderedList = true;
      }
      result.push(`<li>${trimmed.substring(2)}</li>`);
      continue;
    }
    
    // Ordered lists
    const matchOrdered = trimmed.match(/^(\d+)\.\s(.*)/);
    if (matchOrdered) {
      if (inUnorderedList) {
        result.push("</ul>");
        inUnorderedList = false;
      }
      if (!inOrderedList) {
        result.push('<ol class="md-ol">');
        inOrderedList = true;
      }
      result.push(`<li>${matchOrdered[2]}</li>`);
      continue;
    }
    
    // If list was active but line is empty
    if (inUnorderedList && trimmed === "") {
      result.push("</ul>");
      inUnorderedList = false;
      continue;
    }
    if (inOrderedList && trimmed === "") {
      result.push("</ol>");
      inOrderedList = false;
      continue;
    }
    
    // Normal text lines
    if (trimmed !== "") {
      if (inUnorderedList) {
        result.push("</ul>");
        inUnorderedList = false;
      }
      if (inOrderedList) {
        result.push("</ol>");
        inOrderedList = false;
      }
      result.push(`<p>${line}</p>`);
    } else {
      result.push("<br />");
    }
  }
  
  if (inUnorderedList) result.push("</ul>");
  if (inOrderedList) result.push("</ol>");
  
  return result.join("\n").replace(/(<br \/>\s*){2,}/g, "<br />");
}
