import csv
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from bb_products.models import BBProduct
from database_assessment.utils import csv_reader


def write_product_lookup_result(zip_codes, queryset):
    key = 'product'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="product_lookup_result.csv"'
    writer = csv.writer(response)
    writer.writerow(['Zip', 'Product', 'Recorded', 'ORG User', 'Modified User'])

    for zip in zip_codes:
        query_obj = queryset.filter(zip_code__exact=zip).first()
        writer.writerow(
            [f'="{query_obj.zip_code}"', getattr(query_obj, key), query_obj.return_recorded,
             query_obj.org_user, query_obj.modified_user]) \
            if query_obj else writer.writerow([f'="{zip}"', 'N/A', 'N/A', 'N/A', 'N/A'])
    return response


class UploadAndDownloadBBProductCSV(TemplateView):
    template_name = 'bb_products/products.html'

    def return_message(self, request, msg, error=False):
        messages.error(request, msg) if error else messages.success(request, msg)
        return render(self.request, self.template_name)

    # for rollback transaction
    @transaction.atomic()
    def post(self, request):
        csv_file_download = request.FILES.get('csv_file_download', None)
        csv_file_upload = request.FILES.get('csv_file_upload', None)
        if csv_file_download:
            dict_zip_codes = csv_reader(csv_file_download)
            zip_codes = [str(d['Zip']) for d in dict_zip_codes if 'Zip' in d]
            bb_products = BBProduct.objects.filter(zip_code__in=zip_codes)
            return write_product_lookup_result(zip_codes=zip_codes, queryset=bb_products)

        if csv_file_upload:
            data_from_csv = csv_reader(csv_file_upload)

            # validate data from csv
            valid_data_from_csv = []
            for d in data_from_csv:
                if d.get("Zip") == 'N/A' or d.get("Product") == 'N/A' or d.get("Recorded") == 'N/A'\
                        or d.get("ORG User") == 'N/A' or d.get("Modified User") == 'N/A':
                    return self.return_message(request=request, msg='Please check your data. \n '
                                                                    'Note: Data must not have N/A and null', error=True)
                if d.get("Modified User") == '':
                    continue
                valid_data_from_csv.append(d)

            zip_codes_from_csv = [d['Zip'] for d in valid_data_from_csv if 'Zip' in d]
            bb_products_from_db = BBProduct.objects.filter(zip_code__in=zip_codes_from_csv).values_list('zip_code',
                                                                                                        flat=True)
            new_data_from_csv = set(zip_codes_from_csv) - set(bb_products_from_db)

            new_data_list = []
            update_data_list = []
            for data in valid_data_from_csv:
                recorded_date = data.pop('Recorded')
                # change date format
                try:
                    date_delta = datetime.strptime(recorded_date, '%m/%d/%y')
                except:
                    return self.return_message(request=request, msg='Please make sure valid date.',
                                               error=True)

                if data.get('Zip') in new_data_from_csv:
                    new_data_list.append(BBProduct(
                        product=data.get('Product'), recorded=date_delta.date(), zip_code=data.get('Zip'),
                        org_user=data.get('ORG User'), modified_user=data.get('Modified User')
                    ))
                else:
                    product_obj = BBProduct.objects.get(zip_code=data.get('Zip'))
                    product_obj.product = data.get('Product')
                    product_obj.recorded = date_delta.date()
                    product_obj.org_user = data.get('ORG User')
                    product_obj.modified_user = data.get('Modified User')

                    update_data_list.append(product_obj)

            # insert new records and update existing records
            if not new_data_list and not update_data_list:
                return self.return_message(request=request, msg='All data is Up-to-date.')
            else:
                BBProduct.objects.bulk_create(new_data_list)
                BBProduct.objects.bulk_update(update_data_list, ['product', 'recorded', 'org_user', 'modified_user'])
                return self.return_message(request=request, msg='Update Successfully.')

