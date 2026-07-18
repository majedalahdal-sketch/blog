/**
 * رفع صور المسودات وربطها بحقل mainImage
 * تشغيل: npx sanity exec attach-story-images.js --with-user-token
 */
import {getCliClient} from 'sanity/cli'
import {readFileSync} from 'node:fs'
import {basename} from 'node:path'

const client = getCliClient({apiVersion: '2024-01-01'})
const MAP = '/private/tmp/claude-502/-Users-majed-Documents-Claude-code-My-Personal-Brand-Social-media/41e966f2-190d-4237-9915-80d6fa96f155/scratchpad/draft-images.json'

async function main() {
  const mapping = JSON.parse(readFileSync(MAP, 'utf8'))
  let ok = 0, skipped = 0, failed = 0
  for (const [slug, path] of Object.entries(mapping)) {
    const id = `drafts.story-${slug}`
    const doc = await client.getDocument(id)
    if (!doc) { console.log(`⚠ لا توجد مسودة: ${slug}`); failed++; continue }
    if (doc.mainImage) { skipped++; continue }
    try {
      const buf = readFileSync(path)
      const asset = await client.assets.upload('image', buf, {filename: `story-${slug}.jpg`})
      await client.patch(id).set({mainImage: {_type: 'image', asset: {_type: 'reference', _ref: asset._id}}}).commit()
      ok++
      console.log(`✓ ${slug}  (${basename(path)})`)
    } catch (e) {
      failed++
      console.log(`✗ ${slug}: ${e.message}`)
    }
  }
  console.log(`\nتم: ${ok} صورة مرفوعة ومربوطة | متخطى (له صورة): ${skipped} | فشل: ${failed}`)
}

main().catch((e) => { console.error(e); process.exit(1) })
