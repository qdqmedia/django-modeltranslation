from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import get_language

from modeltranslation.utils import build_localized_fieldname


class I18nQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None):
        super(I18nQuerySet, self).__init__(model, query, using)
        self.__model_fields = [f.name for f in self.model._meta.fields]

    def _filter_or_exclude(self, negate, *args, **kwargs):
        #TODO: args need be parsed in Q objects
        kwargs = self.__parse_query_dict(kwargs)
        return super(I18nQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

    def order_by(self, *field_names):
        def parse_field(fieldname):
            prefix = ""
            if fieldname[0] == "-":
                prefix = "-"
                fieldname = fieldname[1:]
            return "%s%s" % (prefix, self.__get_translated_name(fieldname))

        field_names = [parse_field(n) for n in field_names]
        return super(I18nQuerySet, self).order_by(*field_names)

    def distinct(self, *field_names):
        field_names = [self.__get_translated_name(n) for n in field_names]
        return super(I18nQuerySet, self).distinct(*field_names)

    def __parse_query_dict(self, d):
        filters = {}
        for k, v in d.items():
            if '__' in k:
                fname, sufix = k.split('__', 1)
                sufix = "__%s" % sufix
            else:
                fname = k
                sufix = ''
            fname = self.__get_translated_name(fname)
            filters["%s%s" % (fname, sufix)] = v
        return filters

    def __get_translated_name(self, name):
        i18n_name = build_localized_fieldname(name, get_language())
        if name in self.__model_fields and i18n_name in self.__model_fields:
            return i18n_name
        return name


class TranslationManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        """
        Returns a patched query set, allowing clever filters
        based in current active language.
        """
        return I18nQuerySet(self.model, using=self._db)
