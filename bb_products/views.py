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
    """
    write and export csv file from zip codes

    Args:
        zip_codes (List[int]): list of zip codes for looking up
        queryset (List[queryset]): list of bb product from database

    Returns:
        HttpResponse(content_type='text/csv')
    """
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

    def return_message(self, request, msg, error=False, content=None):
        """
        render template with message

        Args:
            request (any): request from view
            msg (string): message for user
            error (bool): error or not
            content (any): data to show in template
        """
        messages.error(request, msg) if error else messages.success(request, msg)
        return render(self.request, self.template_name, content)

    # for rollback transaction
    @transaction.atomic()
    def post(self, request):
        """
        1. csv for look up: look up with zip codes in csv and get data from database
        2. csv for update data: update database from csv

        Args:
            request (any): request from view

        Raises:
            TypeError: if csv has 'N/A', raise error and nothing update

        Note:
            If the modified user in a row has not been specified, then the row is ignored.
            If the modified user has been specified and the zip-code does not yet exist in the database,
                then the data for that zip code should be added to the database.
            If the modified user has been specified and the zip-code does exist,
                then the data for that zip-code should be updated in the database.
            If any of the rows to be inserted or updated contains an ‘N/A’ value,
                then the data is not uploaded, and an error is displayed to the user.
            If row’s modified user is not specified, the contents of the rest of the row do not matter.
                It should be skipped regardless.
        """
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

            content = {
                'new_data_list': new_data_list,
                "update_data_list": update_data_list
            }
            # insert new records and update existing records
            if not new_data_list and not update_data_list:
                return self.return_message(request=request, msg='All data is Up-to-date.')
            else:
                BBProduct.objects.bulk_create(new_data_list)
                BBProduct.objects.bulk_update(update_data_list, ['product', 'recorded', 'org_user', 'modified_user'])
                return self.return_message(request=request, content=content, msg='Update Successfully.')

