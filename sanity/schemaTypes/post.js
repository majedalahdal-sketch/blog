import {defineField, defineType} from 'sanity'

export default defineType({
  name: 'post',
  title: 'مقالة',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      title: 'العنوان',
      type: 'string',
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'slug',
      title: 'الرابط (بأحرف لاتينية)',
      type: 'slug',
      options: {source: 'title', maxLength: 96},
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'date',
      title: 'تاريخ النشر',
      type: 'datetime',
      initialValue: () => new Date().toISOString(),
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'category',
      title: 'التصنيف',
      type: 'string',
      options: {
        list: ['مراجعة', 'تدوينة', 'كتاب', 'خاطرة'],
        layout: 'radio',
        direction: 'horizontal',
      },
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'subcategory',
      title: 'التصنيف الفرعي (اختياري)',
      type: 'string',
      description: 'ليس شرطاً للنشر — اتركه فارغاً إن لم يناسب التدوينة',
      options: {
        list: ['مشهد', 'طعم', 'صوت', 'رائحة', 'ملمس'],
        layout: 'radio',
        direction: 'horizontal',
      },
    }),
    defineField({
      name: 'readingTime',
      title: 'مدة القراءة (بالدقائق)',
      type: 'number',
    }),
    defineField({
      name: 'excerpt',
      title: 'المقتطف',
      description: 'وصف قصير يظهر في البطاقات وتحت العنوان الرئيسي',
      type: 'text',
      rows: 3,
    }),
    defineField({
      name: 'pullQuote',
      title: 'الاقتباس البارز',
      description: 'يظهر بالبرتقالي في صفحة المقالة (اختياري)',
      type: 'text',
      rows: 2,
    }),
    defineField({
      name: 'featured',
      title: 'مقالة الواجهة',
      description: 'تتصدّر الصفحة الرئيسية — فعّلها لمقالة واحدة فقط',
      type: 'boolean',
      initialValue: false,
    }),
    defineField({
      name: 'mainImage',
      title: 'صورة المقالة',
      type: 'image',
      options: {hotspot: true},
      description: 'بعد رفع الصورة: افتح قائمتها ثم «Edit hotspot and crop» وحرّك الدائرة إلى بؤرة الصورة',
    }),
    defineField({
      name: 'body',
      title: 'نص المقالة',
      type: 'array',
      of: [
        {
          type: 'block',
          styles: [
            {title: 'فقرة', value: 'normal'},
            {title: 'عنوان فرعي', value: 'h2'},
            {title: 'عنوان أصغر', value: 'h3'},
            {title: 'اقتباس', value: 'blockquote'},
          ],
        },
        {
          type: 'image',
          options: {hotspot: true},
          fields: [
            {
              name: 'caption',
              type: 'string',
              title: 'التعليق (اختياري)',
              description: 'يظهر بخط صغير تحت الصورة',
            },
            {
              name: 'alt',
              type: 'string',
              title: 'الوصف البديل (اختياري)',
              description: 'لمحركات البحث وقارئات الشاشة',
            },
          ],
        },
      ],
    }),
  ],
  preview: {
    select: {title: 'title', subtitle: 'category', media: 'mainImage'},
  },
})
