/**
 * ترحيل مقالات المدونة إلى Sanity — يعمل مرة واحدة:
 *   npx sanity exec migrate.js --with-user-token
 */
import {getCliClient} from 'sanity/cli'
import {readFileSync} from 'node:fs'
import {resolve, dirname} from 'node:path'
import {fileURLToPath} from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const client = getCliClient({apiVersion: '2024-01-01'})

let keyCounter = 0
const key = () => `k${(keyCounter++).toString(36).padStart(6, '0')}`

// تحويل HTML البسيط (p/h2/h3/blockquote/ul) إلى Portable Text
function htmlToBlocks(html) {
  const blocks = []
  const tagRe = /<(p|h2|h3|blockquote|ul)>([\s\S]*?)<\/\1>/g
  let m
  while ((m = tagRe.exec(html))) {
    const [, tag, inner] = m
    if (tag === 'ul') {
      const liRe = /<li>([\s\S]*?)<\/li>/g
      let li
      while ((li = liRe.exec(inner))) {
        blocks.push(block('normal', li[1], 'bullet'))
      }
    } else {
      blocks.push(block(tag === 'p' ? 'normal' : tag, inner))
    }
  }
  return blocks
}

function block(style, innerHtml, listItem) {
  const children = []
  // دعم strong/em والنص العادي
  const parts = innerHtml.split(/(<strong>[\s\S]*?<\/strong>|<em>[\s\S]*?<\/em>)/)
  for (const part of parts) {
    if (!part) continue
    let marks = []
    let text = part
    if (part.startsWith('<strong>')) {
      marks = ['strong']
      text = part.replace(/<\/?strong>/g, '')
    } else if (part.startsWith('<em>')) {
      marks = ['em']
      text = part.replace(/<\/?em>/g, '')
    }
    text = text.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    if (text) children.push({_type: 'span', _key: key(), text, marks})
  }
  const b = {_type: 'block', _key: key(), style, markDefs: [], children}
  if (listItem) b.listItem = listItem
  return b
}

const posts = JSON.parse(readFileSync(resolve(here, '../_export/posts.json'), 'utf8'))
// نفس الترتيب الأصلي: الأحدث أولاً بفوارق ثوانٍ
const order = ['fi-madih-al-but', 'al-imarah-ka-thakirah', 'lughat-al-samt', 'kharait-al-dakhil', 'al-harf-wal-mana']

async function main() {
  for (const p of posts) {
    const idx = order.indexOf(p.slug)
    const sec = idx >= 0 ? 7 - idx : 3
    console.log(`⏫ ${p.slug} …`)

    let imageRef
    try {
      const buf = readFileSync(resolve(here, `../assets/images/${p.slug}.png`))
      const asset = await client.assets.upload('image', buf, {filename: `${p.slug}.png`})
      imageRef = {_type: 'image', asset: {_type: 'reference', _ref: asset._id}}
    } catch (e) {
      console.warn(`   ⚠ صورة ${p.slug}: ${e.message}`)
    }

    await client.createOrReplace({
      _id: `post-${p.slug}`,
      _type: 'post',
      title: p.title,
      slug: {_type: 'slug', current: p.slug},
      date: `2026-07-09T15:55:0${sec}.000Z`,
      category: p.category,
      subcategory: p.subcategory || undefined,
      readingTime: p.reading_time ? Math.round(p.reading_time) : undefined,
      excerpt: p.excerpt || '',
      pullQuote: p.pull_quote || undefined,
      featured: !!p.is_featured,
      mainImage: imageRef,
      body: htmlToBlocks(p.content || ''),
    })
    console.log(`   ✓ تم`)
  }
  console.log('اكتمل الترحيل ✓')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
